from fastapi import HTTPException
import os
import httpx
import logging

async def notification_server_communication(attempt_id:str,
                                            emp_no:str,
                                            client_id:str,
                                            service_name:str,
                                            data:str):
    """
    Communicates with the notification server to send a data.
    Authentication attempt to a push notification server, which forwards data to user's mobile application.
    Args:
    - attempt_id:  attempt identification ID
    - emp_no: employee identification number
    - client_id: client_id of registered service
    - challenge: the cryptographic challenge data to be sent to the user's mobile application, encoded as a hex string
    Returns:
    - JSON: response
    """
    url = str(os.getenv("PUSH_SERVER_URL"))
    headers = {
        "Content-Type" : "application/json",
        "Accept" : "application/json"
    }
    
    data = {
        "message" : "OneCard Login Success",
        "attempt_id" : str(attempt_id),
        "emp_no" : str(emp_no),
        "client_id" : str(client_id),
        "data" : str(data),
        "service_name" : str(service_name),
        "status" : 200
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url=url,
                                         headers=headers,
                                         json=data,
                                         timeout=5.0)
        response.raise_for_status() 
        
        return response.json()
    
    except httpx.TimeoutException:
            logging.error("Notification Sever request Timeout")
            raise HTTPException(status_code=504, detail="Server Timeout: The server is not responding")
    except httpx.ConnectError:
            logging.error("Push server connection failed")
            raise HTTPException(status_code=503, detail="Connection failed - The server might be down or unreachable")
    except httpx.HTTPStatusError as e:
            logging.error(f"Notification Server returend status code:{e.response.status_code}")
            raise HTTPException(status_code=e.response.status_code, detail=f"Server returned status code:{e.response.status_code}")
    except httpx.RequestError as e:
            logging.error(f"Push server request error: {str(e)}")
            raise HTTPException(status_code=502, detail=f"Request error: {str(e)}")
    except Exception as e:
            logging.error(f"Unexpected error in push server communication: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")