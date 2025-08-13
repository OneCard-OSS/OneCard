import os
import httpx
import logging

async def notification_server_communication(attempt_id:str,
                                      emp_no:str,
                                      client_id:str,
                                      challenge:str):
    """
    Args:
    - attempt_id:  attempt identification ID
    - emp_no: employee identification number
    - client_id: 
    - challenge: 
    Returns:
    - 
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
        "challenge" : str(challenge),
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
        return {
            "status" : 504, # Gateway Timeout
            "message" : "Server Timeout: The server is not responding"
        }
    except httpx.ConnectError:
        logging.error("Push server connection failed")
        return {
            "status": 503,  # Service Unavailable
            "message": "Connection failed - The server might be down or unreachable"
        }
    except httpx.HTTPStatusError as e:
        logging.error(f"Notification Server returend status code:{e.response.status_code}")
        return {
            "status" : 503,
            "message" : f"Sever returned status code:{e.response.status_code}",
            "response_text" : e.response.text
        }
    except httpx.RequestError as e:
        logging.error(f"Push server request error: {str(e)}")
        return {
            "status": 502,  # Bad Gateway
            "message": f"Request error: {str(e)}"
        }

    except Exception as e:
        logging.error(f"Unexpected error in push server communication: {str(e)}")
        return {
            "status": 500,  # Internal Server Error
            "message": f"Unexpected error: {str(e)}"
        }