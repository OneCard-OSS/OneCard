require('dotenv').config();

const http = require('node:http');
const { Server } = require("socket.io");
const jwt = require('jsonwebtoken');

const PORT = process.env.PORT || 3000;
const JWT_SECRET = process.env.JWT_SECRET;
const ALLOWED_SUBNETS = process.env.ALLOWED_SUBNETS ? process.env.ALLOWED_SUBNETS.split(',') : [];

if (!JWT_SECRET) {
    console.error('[ERROR] JWT_SECRET environment variable is not set. Server cannot start.');
    process.exit(1);
}

const express = require('express');
const app = express();
const httpServer = http.createServer(app);
const io = new Server(httpServer, {
    cors: {
        origin: "*",
        methods: ["GET", "POST"]
    }
});

// JSON 파싱 미들웨어 추가
app.use(express.json());

// 접속 중인 사용자 관리
// Map<emp_no, socket> 형식으로 저장하여 사용자 ID로 소켓을 검색
const connectedUsers = new Map();

// --- 미들웨어 ---

/**
 * 내부 IP 대역에서만 접속을 허용하는 미들웨어
 */
const ipFilterMiddleware = (req, res, next) => {
    // ALLOWED_SUBNETS이 비어있으면 IP 필터링을 건너뜁니다.
    if (ALLOWED_SUBNETS.length === 0)
        return next();

    const clientIp = req.ip || req.connection.remoteAddress;
    const formattedIp = clientIp.includes('::ffff:') ? clientIp.split(':').pop() : clientIp;

    const isAllowed = ALLOWED_SUBNETS.some(subnet => formattedIp.startsWith(subnet.trim()));

    if (!isAllowed) {
        console.warn(`[SECURITY] Access denied for IP address: ${formattedIp}`);
        return res.status(403).json({ message: 'Access denied: IP address not allowed' });
    }
    next();
};

/**
 * Socket.io 연결 시 JWT 토큰을 검증하는 미들웨어
 */
io.use((socket, next) => {
    try {
        // 클라이언트에서 보낸 Authorization 헤더에서 토큰을 추출합니다.
        const token = socket.handshake.headers.authorization?.split(' ')[1];

        if (!token) {
            return next(new Error('Authentication error: No token provided.'));
        }

        // 토큰을 검증합니다.
        jwt.verify(token, JWT_SECRET, (err, decoded) => {
            if (err) {
                console.error('[AUTH] JWT verification failed:', err.message);
                return next(new Error('Authentication error: Invalid token'));
            }
            // 검증 성공 시, 소켓 객체에 사용자 정보를 추가합니다.
            console.log('[JWT] authorized user: ', decoded);
            socket.user = decoded.sub;
            next();
        });

    } catch (error) {
        console.error('[AUTH] Authentication processing error:', error);
        next(new Error('Authentication processing failed due to server error'));
    }
});


// --- 라우팅 ---
app.get('/', (req, res) => {
    // 서버 구동 여부 확인
    res.send('onecard-pushsvr/1.0');
});

/**
 * 푸시 알림을 전송하는 POST 엔드포인트
 * 내부망에서만 접근 가능하도록 IP 필터 미들웨어 적용
 */
app.post('/push', ipFilterMiddleware, (req, res) => {
    const { message, emp_no, attempt_id, client_id, data, service_name, status } = req.body;

    if (message === undefined || emp_no === undefined || attempt_id === undefined || client_id === undefined || data === undefined || service_name === undefined || status === undefined) {
        return res.status(400).json({ message: 'Required parameters missing: message, emp_no, attempt_id, client_id, data, service_name, status' });
    }

    // 이미 접속 중인 사용자인지 여부 확인
    const targetSocket = connectedUsers.get(emp_no);

    if (targetSocket) {
        // 사용자가 접속 중이면 'push_notification' 이벤트를 전송합니다.
        targetSocket.emit('push_notification', { message, emp_no, attempt_id, client_id, data, service_name });
        console.log(`[PUSH] Notification sent to user ${emp_no}: ${message}`);
        res.status(200).json({ success: true, message: 'Push notification sent successfully' });

    } else {
        // 사용자가 접속 중이 아니면 실패 응답을 보냅니다.
        console.log(`[PUSH] User ${emp_no} is not connected. Cannot send notification.`);
        res.status(404).json({ success: false, message: 'User is not currently connected' });
    }
});


// --- Socket.io 이벤트 핸들러 ---

io.on('connection', (socket) => {
    const userId = socket.user;
    const overwrite = socket.handshake.query.overwrite === 'true';

    console.log(`[CONNECTION] User ${userId} attempting to connect... (overwrite: ${overwrite})`);

    // emp_no의 형식 검사(falsy 또는 빈 문자열)
    if (!userId || typeof userId !== 'string' || userId.trim() === '') {
        console.warn(`[CONNECTION] Invalid userId provided: ${userId}`);
        socket.emit('connection_rejected', { message: 'Invalid userId provided' });
        socket.disconnect(true);
        return;
    }

    // 이미 동일한 사용자가 접속 중인지 확인
    if (connectedUsers.has(userId)) {

        if (overwrite) {
            // 기존 연결을 종료하고 새로운 연결로 대체
            const oldSocket = connectedUsers.get(userId);
            oldSocket.disconnect(true); // 기존 소켓 연결 강제 종료
            console.log(`[SESSION] Terminating existing session for user ${userId} and replacing with new session`);

        } else {
            // overwrite=false 이면 연결 거부
            console.warn(`[CONNECTION] Connection rejected - User ${userId} is already connected`);
            socket.emit('connection_rejected', { message: 'Already connected from another device' });
            socket.disconnect(true);
            return;
        }
    }

    // 새로운 사용자 연결 처리
    connectedUsers.set(userId, socket);
    console.log(`[CONNECTION] User ${userId} connected successfully (Active users: ${connectedUsers.size})`);
    socket.emit('connected', { message: 'Successfully connected to push notification server' });


    // 연결 종료 이벤트 처리
    socket.on('disconnect', (reason) => {
        // 해당 소켓이 현재 접속 목록에 있는 소켓과 일치하는 경우에만 제거
        if (connectedUsers.get(userId) === socket) {
            connectedUsers.delete(userId);
            console.log(`[DISCONNECT] User ${userId} disconnected (Reason: ${reason}, Active users: ${connectedUsers.size})`);
        }
    });
});


// --- 서버 실행 ---
httpServer.listen(PORT, () => {
    console.log(`OneCard Push notification relay server started on port ${PORT}`);
    console.log(`   - Push endpoint: [POST] http://localhost:${PORT}/push`);
    console.log(`   - Socket connection: ws://localhost:${PORT}`);
});
