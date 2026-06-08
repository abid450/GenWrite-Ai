# apps/content/openai_client.py
import openai
import logging
import time
from typing import Dict, Any, Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class OpenAIClient:
    """OpenAI API Client for content generation"""
    
    def __init__(self):
        """Initialize OpenAI client with settings"""
        openai.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self.default_max_tokens = settings.OPENAI_MAX_TOKENS
        self.default_temperature = settings.OPENAI_TEMPERATURE
        self.timeout = getattr(settings, 'OPENAI_TIMEOUT', 30)
        self.max_retries = getattr(settings, 'OPENAI_MAX_RETRIES', 3)
    
    def generate_content(
        self,
        prompt: str,
        content_type: str,
        parameters: Optional[Dict] = None
    ) -> Dict[str, Any]:
        # Prepare system prompt based on content type
        system_prompt = self._get_system_prompt(content_type)
        
        # Merge parameters
        params = {
            'temperature': self.default_temperature,
            'max_tokens': self.default_max_tokens,
            **parameters
        }
        
        # Retry logic
        for attempt in range(self.max_retries):
            try:
                response = openai.ChatCompletion.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=params['temperature'],
                    max_tokens=params['max_tokens'],
                    timeout=self.timeout
                )
                
                content = response.choices[0].message.content
                tokens_used = response.usage.total_tokens
                
                logger.info(f"Content generated successfully. Tokens used: {tokens_used}")
                
                return {
                    'content': content,
                    'tokens_used': tokens_used,
                    'model': self.model
                }
                
            except openai.error.RateLimitError as e:
                logger.warning(f"Rate limit hit (attempt {attempt + 1}): {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise
                    
            except openai.error.APIConnectionError as e:
                logger.error(f"API connection error: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise
                    
            except openai.error.AuthenticationError as e:
                logger.error(f"Authentication error: {str(e)}")
                raise
                
            except openai.error.OpenAIError as e:
                logger.error(f"OpenAI error: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise
    
    def _get_system_prompt(self, content_type: str) -> str:
        """Get system prompt based on content type"""
        
        prompts = {
            'blog': """You are an expert blog writer. Write engaging, informative, 
            and SEO-friendly blog posts. Use proper headings, subheadings, and 
            maintain a conversational tone. Include relevant examples and 
            practical tips.""",
            
            'article': """You are a professional article writer. Write well-researched, 
            factual, and comprehensive articles. Use proper structure with 
            introduction, body paragraphs, and conclusion.""",
            
            'cover_letter': """You are a professional cover letter writer. Write 
            compelling, personalized cover letters that highlight the candidate's 
            strengths and match the job requirements.""",
            
            'social': """You are a social media content creator. Write engaging, 
            click-worthy posts optimized for social media platforms. Use 
            appropriate hashtags and emojis.""",
            
            'email': """You are an email marketing expert. Write professional, 
            persuasive emails with clear call-to-action. Use proper email 
            structure and formatting.""",
            
            'product_desc': """You are a product description writer. Write 
            compelling, detailed product descriptions that highlight features, 
            benefits, and unique selling points.""",
            
            'ad_copy': """You are an advertising copywriter. Write persuasive, 
            action-oriented ad copy that converts. Focus on benefits and 
            call-to-action.""",
            
            'seo_meta': """You are an SEO expert. Write optimized meta titles 
            and descriptions that improve click-through rates. Keep titles 
            under 60 characters and descriptions under 160 characters.""",
            
            'press_release': """You are a PR professional. Write professional 
            press releases with proper format: headline, dateline, body, 
            boilerplate, and contact information.""",
            
            'script': """You are a video script writer. Write engaging scripts 
            with proper scene descriptions, dialogue, and timing notes."""
        }
        
        return prompts.get(content_type.lower(), prompts.get('blog'))
    
    def generate_with_template(
        self,
        template: str,
        variables: Dict[str, str],
        content_type: str
    ) -> Dict[str, Any]:
        """
        Generate content using a template
        
        Args:
            template: Template string with placeholders
            variables: Variables to replace in template
            content_type: Type of content
        
        Returns:
            Dict with generated content
        """
        # Replace variables in template
        filled_prompt = template
        for key, value in variables.items():
            filled_prompt = filled_prompt.replace(f"{{{{{key}}}}}", str(value))
        
        return self.generate_content(filled_prompt, content_type)