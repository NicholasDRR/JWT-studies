from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi.exceptions import HTTPException
from fastapi import status
from jose import JWTError, jwt
from datetime import datetime, timedelta
from decouple import config

from app.db.models import UserModel
from app.schemas import User
from passlib.context import CryptContext


SECRET_KEY = config('SECRET_KEY')
ALGORITHM = config('ALGORITHM')

crypt_context = CryptContext(schemes=['sha256_crypt'])


class UserUseCases:
    
    def __init__(self, db_session = Session):
       self.db_session = db_session
       
    def user_register(self, user: User):
        
        user_model = UserModel(
            username=user.username,
            password=crypt_context.hash(user.password)
        )
        
        try:
            self.db_session.add(user_model)
            self.db_session.commit()
            
        except IntegrityError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"msg": "User already exists"})
            
            
    def user_login(self, user: User, expires_in: int = 30):
        
        user_on_db = self.db_session.query(UserModel).filter_by(username=user.username).first()
        
        if not user_on_db:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password!")
        
        if not crypt_context.verify(user.password, user_on_db.password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password!")
        
        exp = datetime.utcnow() + timedelta(minutes=expires_in)
        

        payload = {
            'sub': user.username,
            'exp': exp
        }
        
        access_token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        
        return {
            'access_token': access_token,
            'expires_data': exp.isoformat()
        }
    
    def verify_token(self, access_token):
        
        try:
            data = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token!")
        
        user_on_db = self.db_session.query(UserModel).filter_by(username=data['sub']).first()
        
        if not user_on_db:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token!")