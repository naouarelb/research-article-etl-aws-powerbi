# 📊 Analysis of Scientific Research Articles in Morocco on AWS  

🚀 Automating the analysis of scientific publications with a scalable **data pipeline on AWS**.  



## 1️⃣ Introduction  
The project **"Analysis of Scientific Research Articles in Morocco on AWS Cloud"** is an innovative initiative that automates the analysis of Moroccan scientific publications indexed on **Scopus**.  

With a robust AWS data pipeline, this project enables:  
- 🔍 Exploring collaboration networks between Moroccan and international authors  
- 🌍 Identifying the most common languages in scientific publications  
- 📈 Detecting thematic trends and the most active research areas  
- 🎯 Providing actionable insights for researchers, institutions, and policymakers  


## 2️⃣ Why is this project cool?  
- 💡 **Innovation:** Leveraging AWS Cloud to automate large-scale scientific data analysis  
- 🌍 **Impact:** Contributing to a better understanding of Morocco’s scientific research ecosystem  
- 📈 **Scalability:** Modular design for extending analysis to other countries or platforms  
- 📊 **Visualization:** Interactive dashboards for intuitive data exploration  


## 3️⃣ Data  
The data comes from the **Scopus platform**, which catalogs and indexes scientific articles published worldwide from 1913 to the present.  

![Scopus logo](Images/scopus.png)  


## 4️⃣ Project Architecture  
The pipeline is designed to be **scalable, secure, and efficient**:  

![Architecture](Images/architecture.png)  



## 5️⃣ Key Components  
- 📥 **Data Collection:** Extracting data from Scopus via exports  
- 💾 **Storage:** Amazon S3 for raw and processed data  
- ⚙️ **Processing:** Data transformation with AWS Glue and Lambda  
- 📊 **Analysis:** Querying and cataloging with Amazon Athena  
- 📈 **Visualization:** Interactive dashboards built with Power BI (Direct Query mode)  
- 🧩 **Orchestration:** Workflow automation with AWS Glue Workflows  



## 6️⃣ Tech Stack  
- ☁️ **Cloud:** AWS (S3, Glue, Lambda, Athena)  
- 💻 **Languages:** Python, SQL, Spark  
- 🛠️ **Tools:** Terraform (IaC), Power BI Desktop  



## 7️⃣ How to Use This Project  

⚠️ **Prerequisites:**  
- AWS account  
- Terraform 1.0+  
- Visual Studio Code  
- Scopus account (to extract data)  

**1. Clone the repository**  
```bash
git clone https://github.com/nwara5/ANALYSIS-OF-SCIENTIFIC-RESEARCH-ARTICLES-IN-MOROCCO-ON-AWS.git
```

**2. Configure AWS credentials:**
`aws configure`

**3. Launch Terraform to create the cloud infrastructure**

● `terraform init` to initialize Terraform.   
● `terraform plan plan.tfplan` to create the Terraform plan.   
● `terraform apply plan.tfplan` to apply the Terraform plan.   


**4. Connect AWS Athena with Power BI Desktop via ODBC**  
Configure ODBC to connect to AWS Athena via Power BI in Direct Query mode (See [AWS Documentation](https://docs.aws.amazon.com/athena/latest/ug/odbc-v2-driver.html))

**5. Visualize the dashboard:**  
<p align="center">
  <img src="Images\Screenshot 2025-02-10 030109.png" alt="Dashboard 1" width="30%">
  <img src="Images\Screenshot 2025-02-10 030235.png" alt="Dashboard 2" width="30%">
  <img src="Images\Screenshot 2025-02-10 030433.png" alt="Dashboard 3" width="30%">
</p>
<p align="center">
  <img src="Images\Screenshot 2025-02-10 030448.png" alt="Dashboard 4" width="30%">
  <img src="Images\Screenshot 2025-02-10 030511.png" alt="Dashboard 5" width="30%">
  <img src="Images\Screenshot 2025-02-10 030532.png" alt="Dashboard 6" width="30%">
</p>
<p align="center">
  <img src="Images\Screenshot 2025-02-10 030628.png" alt="Dashboard 7" width="30%">
  <img src="Images\Screenshot 2025-02-10 031837.png" alt="Dashboard 8" width="30%">

</p>

## 👤 Author
Naouar EL BOUMASHOULI




