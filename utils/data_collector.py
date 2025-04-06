import os
import json
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from tqdm import tqdm
import time

# Load environment variables
load_dotenv()

# GraphQL API endpoint
GRAPHQL_API = 'https://universitycompare.com/api/graphql'

# Maximum number of concurrent requests
MAX_CONCURRENT_REQUESTS = 50

# Batch size for processing course details
BATCH_SIZE = 100

# Maximum retries for failed requests
MAX_RETRIES = 3

# Retry delay in seconds
RETRY_DELAY = 1

class EducationDataCollector:
    def __init__(self):
        self.session = None
        self.universities = []
        self.courses = []
        self.course_details = {}
        self.semaphore = None
        self.retry_semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        self.semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
            
    async def fetch_all_data(self):
        """Fetch all universities, courses, and course details using parallelism"""
        print("Starting data collection...")
        start_time = time.time()
        
        # Fetch all universities
        await self.fetch_all_universities()
        print(f"Fetched {len(self.universities)} universities")
        
        # Fetch courses for each university in parallel
        print("Fetching courses for all universities...")
        tasks = []
        for university in self.universities:
            tasks.append(self.fetch_university_courses(university["slug"]))
        
        # Use tqdm to show progress
        for task in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Fetching university courses"):
            await task
            
        print(f"Fetched {len(self.courses)} courses")
        
        # Fetch detailed information for courses in batches
        print("Fetching detailed course information...")
        for i in range(0, len(self.courses), BATCH_SIZE):
            batch = self.courses[i:i + BATCH_SIZE]
            tasks = []
            for course in batch:
                tasks.append(self.fetch_course_details_with_retry(course["slug"]))
            
            # Process batch in parallel
            await asyncio.gather(*tasks)
            print(f"Processed batch {i//BATCH_SIZE + 1}/{(len(self.courses) + BATCH_SIZE - 1)//BATCH_SIZE}")
            
        print(f"Fetched details for {len(self.course_details)} courses")
        
        # Save the collected data
        await self.save_data()
        
        end_time = time.time()
        print(f"Data collection completed in {end_time - start_time:.2f} seconds!")
        
    async def fetch_all_universities(self):
        """Fetch all universities using pagination"""
        page = 1
        has_more_pages = True
        
        while has_more_pages:
            print(f"Fetching universities page {page}...")
            
            query = """
            query getUniversities(
              $product: Product,
              $name: String,
              $typeIds: [Int] = null,
              $locationIds: [Int],
              $page: Int,
              $limit: Int = 20,
              $offset: Int
            ) {
              universities(
                product: $product,
                name: $name,
                type_ids: $typeIds,
                location_ids: $locationIds,
                page: $page,
                limit: $limit,
                offset: $offset
              ) {
                data {
                  id
                  name
                  logo
                  paid_features
                  stats {
                    recommended_percentage
                  }
                  saved
                  slug
                  privacy_policy_url
                  order
                  undergraduate: profile(product: UNDERGRADUATE) {
                    external_url
                    external_prospectus_url
                    cover_image
                    external_events_url
                  }
                  postgraduate: profile(product: POSTGRADUATE) {
                    external_url
                    external_prospectus_url
                    cover_image
                    external_events_url
                  }
                }
                filters {
                  name
                  values {
                    id
                    count
                  }
                }
                per_page
                current_page
                has_more_pages
                total
              }
            }
            """
            
            variables = {
                "product": "UNDERGRADUATE",
                "name": "",
                "typeIds": None,
                "locationIds": [],
                "page": page,
                "limit": 20,
                "offset": (page - 1) * 20
            }
            
            try:
                async with self.semaphore:
                    async with self.session.post(
                        GRAPHQL_API,
                        json={"query": query, "variables": variables}
                    ) as response:
                        if response.status != 200:
                            print(f"Error fetching universities: {response.status}")
                            break
                            
                        data = await response.json()
                        
                        if "errors" in data:
                            print(f"GraphQL errors: {data['errors']}")
                            break
                            
                        if "data" in data and "universities" in data["data"]:
                            universities_data = data["data"]["universities"]
                            
                            # Add universities to our list
                            self.universities.extend(universities_data["data"])
                            
                            # Check if there are more pages
                            has_more_pages = universities_data["has_more_pages"]
                            page += 1
                        else:
                            print("Unexpected response format")
                            break
                        
            except Exception as e:
                print(f"Error fetching universities: {e}")
                break
                
    async def fetch_university_courses(self, university_slug: str):
        """Fetch all courses for a university using pagination"""
        page = 1
        has_more_pages = True
        university_courses = []
        
        while has_more_pages:
            query = """
            query getUniversityCourses(
              $slug: String!,
              $degreeLevel: CourseDegreeLevel = ALL_UNDERGRADUATE,
              $tariffMin: Int,
              $tariffMax: Int! = 168,
              $studyMode: CourseStudyMode = null,
              $name: String = null,
              $page: Int,
              $limit: Int,
              $offset: Int
            ) {
              universityCourses(
                slug: $slug,
                degree_level: $degreeLevel,
                min_ucas_tariff: $tariffMin,
                max_ucas_tariff: $tariffMax,
                study_mode: $studyMode,
                name: $name,
                page: $page,
                limit: $limit,
                offset: $offset
              ) {
                id
                slug
                name
                logo
                recommended_percentage
                external_url
                external_prospectus_url
                cover_image
                paid_features
                saved
                privacy_policy_url
                order
                courses {
                  data {
                    id
                    slug
                    name
                    year
                    location
                    study_mode
                    min_ucas_tariff
                    max_ucas_tariff
                    saved
                  }
                  per_page
                  current_page
                  has_more_pages
                  total
                  filters {
                    name
                    values {
                      id
                      count
                    }
                  }
                }
              }
            }
            """
            
            variables = {
                "slug": university_slug,
                "degreeLevel": "ALL_UNDERGRADUATE",
                "tariffMin": 0,
                "tariffMax": 168,
                "studyMode": None,
                "name": None,
                "page": page,
                "limit": 20,
                "offset": (page - 1) * 20
            }
            
            try:
                async with self.semaphore:
                    async with self.session.post(
                        GRAPHQL_API,
                        json={"query": query, "variables": variables}
                    ) as response:
                        if response.status != 200:
                            print(f"Error fetching courses for {university_slug}: {response.status}")
                            break
                            
                        data = await response.json()
                        
                        if "errors" in data:
                            print(f"GraphQL errors for {university_slug}: {data['errors']}")
                            break
                            
                        if "data" in data and "universityCourses" in data["data"]:
                            courses_data = data["data"]["universityCourses"]
                            
                            # Add courses to our list
                            if courses_data.get("courses", {}).get("data"):
                                for course in courses_data["courses"]["data"]:
                                    # Add university information to the course
                                    course["university_slug"] = university_slug
                                    course["university_name"] = next(
                                        (u["name"] for u in self.universities if u["slug"] == university_slug),
                                        None
                                    )
                                    university_courses.append(course)
                                
                                # Check if there are more pages
                                has_more_pages = courses_data["courses"]["has_more_pages"]
                                page += 1
                            else:
                                has_more_pages = False
                        else:
                            print(f"Unexpected response format for {university_slug}")
                            break
                        
            except Exception as e:
                print(f"Error fetching courses for {university_slug}: {e}")
                break
        
        # Add all courses for this university to the main courses list
        self.courses.extend(university_courses)
                
    async def fetch_course_details_with_retry(self, course_slug: str):
        """Fetch course details with retry logic"""
        for attempt in range(MAX_RETRIES):
            try:
                async with self.retry_semaphore:
                    return await self.fetch_course_details(course_slug)
            except Exception as e:
                if attempt == MAX_RETRIES - 1:
                    print(f"Failed to fetch course details for {course_slug} after {MAX_RETRIES} attempts: {e}")
                    return None
                await asyncio.sleep(RETRY_DELAY * (attempt + 1))  # Exponential backoff
        
    async def fetch_course_details(self, course_slug: str):
        """Fetch detailed information for a course"""
        query = """
        query getCourse($courseSlug: String!) {
          course(slug: $courseSlug) {
            id
            slug
            name
            university
            overview
            academic_year
            product
            external_url
            external_scholarships_url
            code
            institution_code
            options {
              study_mode
              duration
              start_date
              campus {
                name
                address
              }
              entry_years
              entry_requirements {
                type
                acceptable
                min_entry
                max_entry
                information
              }
              fees {
                price
                currency
                region
                state
                period
              }
              application_deadline
              external_url
            }
            location {
              address
              postcode
              country
              maps
            }
            saved
          }
        }
        """
        
        variables = {
            "courseSlug": course_slug
        }
        
        try:
            async with self.semaphore:
                async with self.session.post(
                    GRAPHQL_API,
                    json={"query": query, "variables": variables}
                ) as response:
                    if response.status != 200:
                        print(f"Error fetching course details for {course_slug}: {response.status}")
                        return
                        
                    data = await response.json()
                    
                    if "errors" in data:
                        print(f"GraphQL errors for {course_slug}: {data['errors']}")
                        return
                        
                    if "data" in data and "course" in data["data"] and data["data"]["course"]:
                        course_details = data["data"]["course"]
                        self.course_details[course_slug] = course_details
                    
        except Exception as e:
            print(f"Error fetching course details for {course_slug}: {e}")
            raise  # Re-raise for retry logic
            
    async def save_data(self):
        """Save the collected data to JSON files"""
        # Create data directory if it doesn't exist
        os.makedirs("data", exist_ok=True)
        
        print("Saving data to files...")
        
        # Save universities
        with open("data/universities.json", "w") as f:
            json.dump(self.universities, f, indent=2)
            
        # Save courses
        with open("data/courses.json", "w") as f:
            json.dump(self.courses, f, indent=2)
            
        # Save course details
        with open("data/course_details.json", "w") as f:
            json.dump(self.course_details, f, indent=2)
            
        # Create a structured dataset for inference
        structured_data = self.create_structured_dataset()
        with open("data/structured_dataset.json", "w") as f:
            json.dump(structured_data, f, indent=2)
            
        print("Data saved successfully!")
            
    def create_structured_dataset(self) -> List[Dict[str, Any]]:
        """Create a structured dataset for inference with available information"""
        print("Creating structured dataset...")
        structured_data = []
        
        for course_slug, details in self.course_details.items():
            # Find the corresponding course in our courses list
            course = next((c for c in self.courses if c["slug"] == course_slug), None)
            
            if not course:
                continue
                
            # Extract entry requirements
            entry_requirements = {}
            if details.get("options") and len(details["options"]) > 0:
                option = details["options"][0]
                
                if option.get("entry_requirements"):
                    for req in option["entry_requirements"]:
                        if req.get("type") and req.get("information"):
                            entry_requirements[req["type"]] = {
                                "acceptable": req.get("acceptable", False),
                                "min_entry": req.get("min_entry"),
                                "max_entry": req.get("max_entry"),
                                "information": req["information"]
                            }
            
            # Extract fees
            fees = {}
            if details.get("options") and len(details["options"]) > 0:
                option = details["options"][0]
                
                if option.get("fees"):
                    for fee in option["fees"]:
                        if fee.get("region") and fee.get("price"):
                            fees[fee["region"]] = {
                                "price": fee["price"],
                                "currency": fee.get("currency", "GBP"),
                                "period": fee.get("period", "year")
                            }
            
            # Create structured course data
            structured_course = {
                "id": details.get("id"),
                "slug": course_slug,
                "name": details.get("name"),
                "university": details.get("university"),
                "overview": details.get("overview"),
                "academic_year": details.get("academic_year"),
                "product": details.get("product"),
                "external_url": details.get("external_url"),
                "external_scholarships_url": details.get("external_scholarships_url"),
                "code": details.get("code"),
                "institution_code": details.get("institution_code"),
                "study_options": [{
                    "study_mode": opt.get("study_mode"),
                    "duration": opt.get("duration"),
                    "start_date": opt.get("start_date"),
                    "campus": opt.get("campus"),
                    "entry_years": opt.get("entry_years"),
                    "entry_requirements": opt.get("entry_requirements"),
                    "fees": opt.get("fees"),
                    "application_deadline": opt.get("application_deadline"),
                    "external_url": opt.get("external_url")
                } for opt in details.get("options", [])],
                "location": details.get("location"),
                "saved": details.get("saved")
            }
            
            structured_data.append(structured_course)
            
        return structured_data

async def main():
    async with EducationDataCollector() as collector:
        await collector.fetch_all_data()

if __name__ == "__main__":
    asyncio.run(main()) 