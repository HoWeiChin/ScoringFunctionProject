# ScoringFunctionProject

## Project Summary
Lab group Information: https://www.a-star.edu.sg/bii/research/bmad/sldd  
Project Goal: To build an end-to-end Machine Learning Pipeline to predict how well a ligand binds to a enzyme (protein).  
  
The project would be conducted in 2 phases: 
1. Data collection from the Mutein Database (https://muteindb.genome.tugraz.at/muteindb-web-2.0/faces/init/index.seam), in particular, protein mutant sequences and their meta information was collected. Meta information includes reaction type, organism class a protein belongs to, a protein's substrate and its corresponding product.  
2. Experimentation with Machine Learning/Deep Learning Models.

## Data Collection Phase
### Key Points
1. The Mutein Database has no REST API; data cannot be collected programmatically by doing HTTP requests and persisting the data into a database. To collect the data, someone would need to manually search and navigate the database's web interface to gather the relevant data.  
2. To avoid manual labour, a Python-based webscrapper (see scrapper.py in this repo) was implemented to collect the data. The Selenium and the Beautiful Soup libraries were chosen for this purpose. Selenium is usually used for automating the testing of front end interfaces, by simulating how users would interact with an interface. But, for our project, Selenium is instead used to perform manual navigation of Mutein's website. Simultaneously, Beautiful Soup will parse the HTML webpages and acquire the dataset we desire. In short, the data collector simply just runs scrapper.py to completion without doing any tedious manual work.  
3. The data collected was stored in 5 csv files:  
   1. wt_table.csv: contains wildtype code and wildtype fasta sequence.
   2. mt_table.csv: contains mutant code, organism, its corresponding wildtype code and mutant fasta sequence.
   3. rxn_table.csv: contains rxn_id, mutant code, substrate of rxn, product of rxn, the type of rxn, EC code and rxn co-protein.
   4. pub_table.csv: contains pubmed_id, rxn_id and mutant code.
   5. mt_act_table.csv: contains rxn_id, mutant code, relative activity value, activity value and activity unit

4. And finally, full_data.csv which is a merger of rxn_table, mt_act_table and pub_table. Full_data.csv contains mutant code, wildtype code, mutant sequence, rxn_id, substate, product, rxn type, EC code, co_protein, relative activity, activity, activity unit and pubmed id.
5. Realising that the tables have common data columns, we can describe relationships between them. Thus, I designed a data model: https://dbdiagram.io/d/604efc93fcdcb6230b24250f. Each box represents one of the csv files. For example, wildtype box corresponds to wt_table.csv. Each attribute of the box corresponds to a column of the csv file.
6. If you access the data model url and hover over the line connecting wildtype and mutant boxes, you notice something which looks like "1 ---- *", this means
1 wildtype data can be related to multiple mutant data and so forth. I tried to model the data in a way which reflects actual Biology, for example we can generate many mutants from a 1 wildtype protein sequence. Finally, a line implies a foreign key between 2 tables.  
7. For the wildtype data, the attribute "wt_code" is bold, this means the attribute is a primary key. Primary key is a field which can uniquely identifies a row of data. Since wildtype code is unique, it must uniquely identify a row of data in the wildtype table.
