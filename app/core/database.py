import os
import logging
from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

Base = declarative_base()

class Publication(Base):
    __tablename__ = "publications"
    
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    publication_date = Column(DateTime, nullable=False)
    competence = Column(String(7), nullable=False, index=True)  
    original_link = Column(Text, nullable=True)
    file_path = Column(Text, nullable=True)
    file_url = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Publication(id={self.id}, title='{self.title[:30]}...', date='{self.publication_date}')>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "publication_date": self.publication_date.strftime("%Y-%m-%d"),
            "competence": self.competence,
            "original_link": self.original_link,
            "file_url": self.file_url,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }

class DatabaseManager:
    def __init__(self):
        db_user = os.getenv("DB_USER", "postgres")
        db_password = os.getenv("DB_PASSWORD", "postgres")
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "natal_prefeitura")
        self.db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        
        try:
            self.engine = create_engine(self.db_url)
            Base.metadata.create_all(self.engine)
            self.Session = sessionmaker(bind=self.engine)
            logger.info("Conexão com o banco de dados estabelecida com sucesso")
        except SQLAlchemyError as e:
            logger.error(f"Erro ao conectar ao banco de dados: {str(e)}")
            raise
    
    def save_publications(self, publications):
        session = self.Session()
        saved_count = 0
        
        try:
            for pub in publications:
                existing = session.query(Publication).filter(
                    Publication.title == pub["title"],
                    Publication.publication_date == pub["date"]
                ).first()
                
                if existing:
                    logger.info(f"Publicação já existe no banco: {pub['title'][:30]}...")
                    continue
                new_publication = Publication(
                    title=pub["title"],
                    publication_date=pub["date"],
                    competence=pub["competence"],
                    original_link=pub.get("link"),
                    file_path=pub.get("file_path"),
                    file_url=pub["file_url"]
                )
                
                session.add(new_publication)
                saved_count += 1
            
            # Commit da transação
            session.commit()
            logger.info(f"{saved_count} publicações salvas no banco de dados")
            
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Erro ao salvar publicações: {str(e)}")
        finally:
            session.close()
        
        return saved_count
    
    def get_all_publications(self):
        session = self.Session()
        try:
            publications = session.query(Publication).order_by(Publication.publication_date.desc()).all()
            return [pub.to_dict() for pub in publications]
        except SQLAlchemyError as e:
            logger.error(f"Erro ao buscar publicações: {str(e)}")
            return []
        finally:
            session.close()
    
    def get_publications_by_competence(self, competence):
        session = self.Session()
        try:
            publications = session.query(Publication).filter(
                Publication.competence == competence
            ).order_by(Publication.publication_date.desc()).all()
            
            return [pub.to_dict() for pub in publications]
        except SQLAlchemyError as e:
            logger.error(f"Erro ao buscar publicações por competência: {str(e)}")
            return []
        finally:
            session.close()

if __name__ == "__main__":
    db_manager = DatabaseManager()
    print("Conexão com o banco de dados estabelecida com sucesso!")