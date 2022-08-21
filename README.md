# Sparkify: Data Lake Project

## Project description
A music streaming startup, Sparkify, has grown their user base and song database and want to move their data warehouse to a data lake. This will allow their analytics team to continue finding insights in what songs their users are listening to.

**Project Goals**:
- build an ETL pipeline that extracts the data from S3
- create a star schema optimized for queries on song play analysis
- process the data using Spark
- load the data back into S3 as a set of dimensional tables
## Project datasets:
- Song Dataset - s3://udacity-dend/song_data
- Log Dataset - s3://udacity-dend/log_data
## Project files: 
- etl.py: reads data from S3, processes that data using Spark, and writes them back to S3
- dl.cfg: contains the AWS credentials
- README.md: provides discussion on the project
## ETL Pipeline:
This project builds an ETL pipeline for a Data Lake hosted on S3. Data is loaded from S3, processed into analytics tables using Spark, and loaded back into S3. This allows the analytics team to continue finding insights in what songs their users are listening to.
## Database schema:
For this project I modeled a star schema that is optimized for queries on song play analysis. This includes the following tables:
#### Fact Table
1. songplays - records in log data associated with song plays i.e. records with page *NextSong*
 - songplay_id
 - start_time
 - user_id
 - level
 - song_id
 - artist_id
 - session_id
 - location
 - user_agent
#### Dimension Tables
2. users - users in the app
 - user_id
 - first_name
 - last_name
 - gender
 - level
3. songs - songs in music database
 - song_id
 - title
 - artist_id
 - year
 - duration
4. artists - artists in music database
 - artist_id
 - name
 - location
 - latitude
 - longitude
5. time - timestamps of records in *songplays* broken down into specific units
 - start_time
 - hour
 - day
 - week
 - month
 - year
 - weekday
 
## How to Run:
1. Add AWS IAM credentials in *dl.cfg* file
2. Specify output path in the *main* function of *etl.py* file 
3. run *etl.py* file