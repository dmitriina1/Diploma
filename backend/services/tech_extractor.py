"""
Utility for extracting technology mentions from text (vacancy descriptions, titles)
"""
import re
from typing import Set

# Common IT technologies and frameworks
TECH_KEYWORDS = {
    # Languages
    "Python", "JavaScript", "TypeScript", "Java", "Kotlin", "Go", "Golang", "Rust",
    "C++", "C#", "PHP", "Ruby", "Swift", "Scala", "Dart", "Elixir", "Clojure",
    
    # Frontend
    "React", "Vue", "Angular", "Svelte", "Next.js", "Nuxt", "Gatsby", "Remix",
    "HTML", "CSS", "SASS", "SCSS", "Tailwind", "Bootstrap", "Material-UI", "Ant Design",
    "Webpack", "Vite", "Rollup", "Parcel", "Redux", "MobX", "Zustand", "Pinia",
    
    # Backend
    "Node.js", "Express", "Fastify", "NestJS", "Django", "Flask", "FastAPI",
    "Spring", "Spring Boot", "Hibernate", "Gin", "Echo", "Laravel", "Symfony",
    "Rails", "Ruby on Rails", "ASP.NET", ".NET", "Fiber",
    
    # Databases
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "Cassandra",
    "Oracle", "SQL Server", "SQLite", "DynamoDB", "CouchDB", "Neo4j",
    "ClickHouse", "TimescaleDB", "InfluxDB",
    
    # DevOps & Cloud
    "Docker", "Kubernetes", "K8s", "Helm", "Terraform", "Ansible", "Jenkins",
    "GitLab CI", "GitHub Actions", "CircleCI", "Travis CI", "AWS", "Azure", "GCP",
    "Nginx", "Apache", "Prometheus", "Grafana", "ELK", "Kibana", "Logstash",
    
    # Message Queues
    "RabbitMQ", "Kafka", "NATS", "ActiveMQ", "ZeroMQ", "Redis Pub/Sub",
    
    # Testing
    "Jest", "Mocha", "Pytest", "JUnit", "TestNG", "Selenium", "Cypress",
    "Playwright", "Postman", "JMeter",
    
    # Mobile
    "React Native", "Flutter", "Xamarin", "Ionic", "SwiftUI", "Jetpack Compose",
    
    # ML/AI
    "TensorFlow", "PyTorch", "Keras", "scikit-learn", "Pandas", "NumPy",
    "OpenCV", "NLTK", "spaCy", "Hugging Face",
    
    # Other
    "Git", "GraphQL", "REST", "gRPC", "WebSocket", "OAuth", "JWT", "SOAP",
    "Microservices", "Agile", "Scrum", "CI/CD", "Linux", "Unix", "Bash",
}

# Normalize variations
TECH_ALIASES = {
    "k8s": "Kubernetes",
    "js": "JavaScript",
    "ts": "TypeScript",
    "postgres": "PostgreSQL",
    "mongo": "MongoDB",
    "elastic": "Elasticsearch",
    "react.js": "React",
    "vue.js": "Vue",
    "node": "Node.js",
    "nextjs": "Next.js",
    "nuxtjs": "Nuxt",
}


def extract_technologies(text: str) -> Set[str]:
    """
    Extract technology mentions from text using keyword matching.
    
    Args:
        text: Text to extract from (vacancy description or title)
        
    Returns:
        Set of normalized technology names
    """
    if not text:
        return set()
    
    text_lower = text.lower()
    found_techs = set()
    
    # Check each technology keyword
    for tech in TECH_KEYWORDS:
        tech_lower = tech.lower()
        # Use word boundaries to avoid partial matches
        pattern = r'\b' + re.escape(tech_lower) + r'\b'
        if re.search(pattern, text_lower):
            found_techs.add(tech)
    
    # Check aliases
    for alias, canonical in TECH_ALIASES.items():
        pattern = r'\b' + re.escape(alias) + r'\b'
        if re.search(pattern, text_lower):
            found_techs.add(canonical)
    
    return found_techs


def extract_from_title(title: str) -> Set[str]:
    """Extract technologies from vacancy title"""
    return extract_technologies(title)


def extract_from_description(description: str) -> Set[str]:
    """Extract technologies from vacancy description"""
    return extract_technologies(description)
