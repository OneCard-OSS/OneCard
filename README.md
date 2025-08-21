### 💳 OneCard 통합 인증 시스템 설치 가이드

OneCard 프로젝트의 전체 시스템을 로컬 또는 서버 환경에 설치하고 실행하는 방법을 안내합니다. 모든 서비스는 Docker Compose를 통해 한 번에 관리됩니다.
📋 사전 준비 사항

설치를 진행하기 전에, 시스템에 다음 소프트웨어들이 설치되어 있어야 합니다.

    Git: 소스 코드를 내려받기 위해 필요합니다.

    Docker: 컨테이너 기술을 사용하여 각 서비스를 격리하고 실행하기 위해 필요합니다.

    Docker Compose: 여러 개의 Docker 컨테이너를 정의하고 한 번에 실행하기 위해 필요합니다.

### 설치 절차
**1. 프로젝트 소스 코드 복제 (Clone)**

가장 먼저, Git을 사용하여 프로젝트의 전체 소스 코드를 내려받습니다.

git clone <프로젝트_저장소_URL>
cd onecard

**2. 환경 변수 설정**

각 서비스는 동작에 필요한 민감한 정보나 설정값들을 .env 파일로부터 읽어옵니다. 프로젝트의 최상위 디렉토리(onecard)에 다음 docker-compose.yml 파일을 생성하고, 각 서비스 디렉토리 내에 .env 파일을 생성하여 내용을 채워야 합니다.

**2-2. onecard-api/.env 파일 생성**

onecard-api 디렉토리 안에 .env 파일을 생성하고 아래 내용을 채워넣으세요. (주의: SECRET KEY들은 반드시 강력한 랜덤 값으로 변경하세요!)

데이터베이스 연결 정보 (docker-compose의 서비스 이름을 호스트로 사용)
DATABASE_URL=postgresql://your_db_user:your_db_password@db:5432/onecard_db

Redis 연결 정보 (docker-compose의 서비스 이름을 호스트로 사용)
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DATABASE=1

푸시 서버 URL (docker-compose의 서비스 이름을 호스트로 사용)
PUSH_SERVER_URL=http://onecard-pushserver:5000/push

JWT 토큰 설정
ACCESS_SECRET_KEY=your_super_strong_access_secret_key
REFRESH_SECRET_KEY=your_super_strong_refresh_secret_key
ALGORITHM=HS256
AT_EXPIRE_MINUTES=15
RT_EXPIRE_MINUTES=129600 # 90일

FastAPI 세션 미들웨어용 비밀 키
SECRET_KEY=your_super_strong_session_secret_key

**2-3. onecard-web/.env 파일 생성**

onecard-web 디렉토리 안에 .env 파일을 생성하고 아래 내용을 채워넣으세요.

FastAPI 세션 미들웨어용 비밀 키
SECRET_KEY=another_strong_session_secret_key

인증 서버 주소 (onecard-api 컨테이너가 사용하는 포트)
AUTH_SERVER_URL=http://onecard-api:8001

**2-4. onecard-pushserver/.env 파일 생성**

onecard-pushserver 디렉토리 안에 .env 파일을 생성하고 필요한 환경 변수를 추가합니다. (예: PORT=5000)

**3. Docker Compose로 전체 시스템 실행**

모든 .env 파일 설정이 완료되었으면, 프로젝트 최상위 디렉토리 (/home/woojinshin/oss/onecard)에서 아래 명령어를 실행하여 모든 서비스를 빌드하고 실행합니다.

docker-compose up -d --build

    -d: 백그라운드에서 실행

    --build: 이미지를 새로 빌드 (최초 실행 시 또는 코드 변경 시 필요)

✅ 실행 확인

    Docker 컨테이너 상태 확인: docker-compose ps 명령어를 실행하여 모든 서비스(db, redis, api, web, pushserver)의 상태가 Up 또는 running인지 확인합니다.

    관리자 페이지 접속: 웹 브라우저에서 http://<서버_IP>:9413/admin 주소로 접속하여 관리자 페이지가 정상적으로 나타나는지 확인합니다.

    API 문서 확인: 웹 브라우저에서 http://<서버_IP>:9414/docs 주소로 접속하여 onecard-api의 Swagger UI가 정상적으로 나타나는지 확인합니다.

🛑 시스템 종료

전체 시스템을 중지하려면, docker-compose.yml 파일이 있는 디렉토리에서 아래 명령어를 실행합니다.

docker-compose down
