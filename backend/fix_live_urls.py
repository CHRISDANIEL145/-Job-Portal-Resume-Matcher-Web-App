from app import create_app
from app.extensions import db
from app.models import CompanyProfile

app = create_app()
with app.app_context():
    print("Connecting to DB:", app.config["SQLALCHEMY_DATABASE_URI"].split("@")[-1])
    db.create_all()
    c1 = CompanyProfile.query.filter_by(company_name="TechCorp Global").first()
    if c1:
        c1.website_url = "https://careers.google.com"
        print("  ✔ Updated TechCorp Global URL to https://careers.google.com")
    
    c2 = CompanyProfile.query.filter_by(company_name="Innovate AI Labs").first()
    if c2:
        c2.website_url = "https://openai.com/careers"
        print("  ✔ Updated Innovate AI Labs URL to https://openai.com/careers")

    db.session.commit()
    print("✔ Company URLs updated successfully!")
