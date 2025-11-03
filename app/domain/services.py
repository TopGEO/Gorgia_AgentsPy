from app.config.settings import settings

class BaseService:
    @staticmethod
    def get_gemini_key() -> str:
        return settings.gemini_api_key

