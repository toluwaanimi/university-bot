def format_course_details(course):
    """
    Format course details in a readable way.
    
    Args:
        course (dict): Course information
        
    Returns:
        str: Formatted course details
    """
    fee = next((f for f in course["fees"] if f["region"] == "England"), {})
    fee_str = f"£{fee.get('price', 'N/A')} per {fee.get('period', 'year')}" if fee else "Fee information not available"
    
    # Format entry requirements
    entry_reqs = []
    for req in course["entry_requirements"]:
        if req["type"] == "UCAS Tariff":
            entry_reqs.append(f"UCAS Tariff: {req['min_entry']} points")
        else:
            entry_reqs.append(f"{req['type']}: {req.get('min_entry', 'N/A')}")
    
    entry_reqs_str = "\n  - ".join(entry_reqs) if entry_reqs else "Not specified"
    
    return f"""
**{course['name']}** at {course['university']}
- Study Mode: {course['study_mode']}
- Duration: {course['duration']}
- Campus: {course['campus']}
- Fees: {fee_str}
- Entry Requirements:
  - {entry_reqs_str}
- [Learn more]({course['external_url']})
"""

def format_course_list(courses):
    """
    Format a list of courses in a readable way.
    
    Args:
        courses (list): List of course dictionaries
        
    Returns:
        str: Formatted course list
    """
    if not courses:
        return "No courses found matching your criteria."
    
    result = "Here are the courses that match your criteria:\n\n"
    for course in courses:
        result += format_course_details(course) + "\n"
    
    return result 