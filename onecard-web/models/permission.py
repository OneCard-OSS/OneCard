from sqlalchemy import Table, Column, Integer, String, ForeignKey
from core.database import Base

"""
Permission Table defining many-to-many relationship between Employee and Services
"""
permission_table = Table('permission', Base.metadata,
                         Column('service_id', Integer, 
                                ForeignKey('services.id', ondelete='CASCADE'), 
                                primary_key=True),
                         Column('emp_no', String(16), 
                                ForeignKey('employee.emp_no', ondelete='CASCADE'), 
                                primary_key=True)
                         )
    
    