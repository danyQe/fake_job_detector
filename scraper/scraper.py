import asyncio
import logging
from typing import Optional
from fastapi import HTTPException
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
import platform
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def is_naukri_url(url: str) -> bool:
    """Check if the URL is from Naukri.com"""
    parsed_url = urlparse(url)
    return 'naukri.com' in parsed_url.netloc

def is_linkedin_url(url: str) -> bool:
    """Check if the URL is from LinkedIn"""
    parsed_url = urlparse(url)
    return 'linkedin.com' in parsed_url.netloc

async def scrape_naukri_job(url: str) -> str:
    """Specialized scraper for Naukri.com job postings"""
    try:
        # Configure browser to focus on main content
        browser_config = BrowserConfig(
            viewport_width=1200,
            viewport_height=800,
            wait_for_selector=".jd-sec",  # Main job description section
            wait_timeout=10000
        )
        
        crawler_config = CrawlerRunConfig(
            cache_mode=CacheMode.NONE,
            browser_config=browser_config
        )
        
        async with AsyncWebCrawler(config=crawler_config) as crawler:
            result = await crawler.arun(url)
            
            if not result.success:
                raise ValueError(f"Failed to scrape Naukri URL: {result.error_message}")
            
            # Extract only the main job content
            content = str(result.markdown)
            
            # Find the main job description section
            start_idx = content.find("## Job description")
            if start_idx == -1:
                start_idx = content.find("Job description")
            
            if start_idx != -1:
                # Get content from job description onwards
                content = content[start_idx:]
                
                # Remove any content after "Posted" or "Register" which indicates the end of main content
                end_idx = min(
                    content.find("Posted") if content.find("Posted") != -1 else len(content),
                    content.find("Register") if content.find("Register") != -1 else len(content)
                )
                content = content[:end_idx].strip()
            
            return content
            
    except Exception as e:
        logger.error(f"Error scraping Naukri job: {str(e)}")
        raise

def _scrape_process(url: str) -> str:
    """Run the scraper in a separate process"""
    # Set event loop policy for this process
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Create a new event loop for this process
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        async def scrape():
            if is_linkedin_url(url):
                raise ValueError(
                    "LinkedIn job postings require login.so it's not supported yet. sorry for the inconvenience.to predict the job posting, please copy and paste the job description in the text area below."
                )
            elif is_naukri_url(url):
                return await scrape_naukri_job(url)
            else:
                # Use default scraper for other URLs
                browser_config = BrowserConfig(
                    viewport_width=1200,
                    viewport_height=800
                )
                
                crawler_config = CrawlerRunConfig(
                    cache_mode=CacheMode.NONE,
                    browser_config=browser_config
                )
                
                async with AsyncWebCrawler(config=crawler_config) as crawler:
                    result = await crawler.arun(url)
                    if not result.success:
                        raise ValueError(f"Failed to scrape URL: {result.error_message}")
                    return str(result.markdown)

        content = loop.run_until_complete(scrape())
        
        # Add content validation
        if len(content.strip()) < 50:
            raise ValueError("Insufficient content found on page")
        
        # Save the content to file
        with open('scraped_text.txt', 'w', encoding='utf-8') as f:
            f.write(content)
            
        return content
        
    except Exception as e:
        logger.error(f"Scraping error in process: {str(e)}")
        raise
    finally:
        loop.close()

async def web_scrape(url: str, proxy: Optional[str] = None) -> str:
    """Scrapes content from a webpage using Crawl4AI.
    
    Args:
        url: The URL of the webpage to scrape.
        proxy: Optional proxy server to use (format: 'http://ip:port' or 'https://ip:port')
        
    Returns:
        A string of the markdown-formatted content of the webpage.
    """
    try:
        logger.debug(f"Starting web scrape for URL: {url}")
        
        # Run the scraper in a separate process
        with ProcessPoolExecutor(max_workers=1) as executor:
            content = await asyncio.get_event_loop().run_in_executor(
                executor,
                _scrape_process,
                url
            )
            
        logger.debug("Scraping completed successfully")
        return content
            
    except Exception as e:
        logger.error(f"Scraping error for URL {url}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error scraping job posting: {str(e)}")

# Helper function to run the async scraper
async def scrape_website(url: str, proxy: Optional[str] = None) -> str:
    """Async wrapper for the web_scrape function"""
    logger.debug("Starting scrape_website function")
    return await web_scrape(url, proxy)