import configparser
import os
import time
from datetime import datetime

from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, col
from pyspark.sql.types import StructType as R, StructField as Fld, DoubleType as Dbl, LongType as Long, \
    StringType as Str, IntegerType as Int, DecimalType as Dec, TimestampType as Stamp

config = configparser.ConfigParser()
config.read("dl.cfg")

os.environ["AWS_ACCESS_KEY_ID"] = config["AWS"]["AWS_ACCESS_KEY_ID"]
os.environ["AWS_SECRET_ACCESS_KEY"] = config["AWS"]["AWS_SECRET_ACCESS_KEY"]


def create_spark_session():
    """ Creates a spark session
    Returns:
        spark session object
    """
    spark = SparkSession \
        .builder \
        .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:2.7.0") \
        .getOrCreate()

    print("Spark session created!")
    return spark


def process_song_data(spark, input_data, output_data):
    """ Loads song data from S3 bucket
        processes song data and creates songs and artist table
        writes the result back to the S3 bucket
    Args:
        spark: spark session object
        input_data: location of S3 bucket with input data
        output_data: location of S3 bucket for output data
    """
    # get filepath to song data file
    song_file_path = "song_data/A/A/A/*.json"
    song_data = os.path.join(input_data, song_file_path)

    # read song data file
    print("Reading song data...")
    df = spark.read.json(song_data, schema=get_song_schema())

    # extract columns to create songs table
    songs_table = df.select("song_id", "title", "artist_id", "year", "duration").dropDuplicates(["song_id"])

    # write songs table to parquet files partitioned by year and artist
    print("Writing songs table...")
    songs_table.write.parquet(output_data + "songs.parquet",
                              partitionBy=["year", "artist_id"],
                              mode="overwrite")

    # extract columns to create artists table
    artists_table = df.selectExpr("artist_id", "artist_name as name", "artist_location as location",
                                  "artist_latitude as latitude",
                                  "artist_longitude as longitude").dropDuplicates(["artist_id"])

    # write artists table to parquet files
    print("Writing artists table...")
    artists_table.write.parquet(output_data + "artists.parquet",
                                mode="overwrite")


def process_log_data(spark, input_data, output_data):
    """ Loads log data from S3 bucket
        processes log data and creates user and time table
        writes the result back to the S3 bucket
    Args:
        spark: spark session object
        input_data: location of S3 bucket with input data
        output_data: location of S3 bucket for output data
    """
    # get filepath to log data file
    log_file_path = "log_data/*/*/*.json"
    log_data = os.path.join(input_data, log_file_path)

    # read log data file
    print("Reading log data...")
    df = spark.read.json(log_data, schema=get_log_schema())

    # filter by actions for song plays
    df = df.filter(df.page == "NextSong")

    # extract columns for users table    
    users_table = df.selectExpr("userId as user_id", "firstName as first_name", "lastName as last_name", "gender",
                                "level").dropDuplicates(["user_id"])

    # write users table to parquet files
    print("Writing users table...")
    users_table.write.parquet(output_data + "users.parquet",
                              mode="overwrite")

    # create timestamp column from original timestamp column
    get_timestamp = udf(lambda x: datetime.fromtimestamp((x / 1000)), Stamp())
    df = df.withColumn("timestamp", get_timestamp(col("ts")))

    # create datetime column from original timestamp column
    get_datetime = udf(lambda x: datetime.fromtimestamp((x / 1000)), Stamp())
    df = df.withColumn("datetime", get_datetime(col("ts")))

    # extract columns to create time table
    time_table = df.selectExpr("timestamp as start_time", "hour(timestamp) as hour", "dayofmonth(timestamp) as day",
                               "weekofyear(timestamp) as week", "month(timestamp) as month", "year(timestamp) as year",
                               "dayofweek(timestamp) as weekday").dropDuplicates(["start_time"])

    # write time table to parquet files partitioned by year and month
    print("Writing time table...")
    time_table.write.parquet(output_data + "time.parquet",
                             partitionBy=["year", "month"],
                             mode="overwrite")

    # read in song data to use for songplays table
    song_data = input_data + "song_data/*/*/*/*.json"
    song_df = spark.read.json(song_data, schema=get_song_schema())

    # extract columns from joined song and log datasets to create songplays table
    song_df.createOrReplaceTempView("song_data")
    df.createOrReplaceTempView("log_data")

    songplays_table = spark.sql("""
                                SELECT monotonically_increasing_id() as songplay_id,
                                ld.timestamp as start_time,
                                year(ld.timestamp) as year,
                                month(ld.timestamp) as month,
                                ld.userId as user_id,
                                ld.level as level,
                                sd.song_id as song_id,
                                sd.artist_id as artist_id,
                                ld.sessionId as session_id,
                                ld.location as location,
                                ld.userAgent as user_agent
                                FROM log_data ld
                                JOIN song_data sd
                                ON (ld.song = sd.title
                                AND ld.length = sd.duration
                                AND ld.artist = sd.artist_name)
                                """)

    # write songplays table to parquet files partitioned by year and month
    print("Writing songplays table...")
    songplays_table.write.parquet(output_data + "songplays.parquet",
                                  partitionBy=["year", "month"],
                                  mode="overwrite")


def get_song_schema():
    """ Creates a schema for song data
    Returns:
        song data schema
    """
    song_schema = R([
        Fld("num_songs", Int()),
        Fld("artist_id", Str()),
        Fld("artist_latitude", Dec()),
        Fld("artist_longitude", Dec()),
        Fld("artist_location", Str()),
        Fld("artist_name", Str()),
        Fld("song_id", Str()),
        Fld("title", Str()),
        Fld("duration", Dbl()),
        Fld("year", Int())
    ])
    return song_schema


def get_log_schema():
    """ Creates a schema for log data
    Returns:
        log data schema
    """
    log_schema = R([
        Fld("artist", Str()),
        Fld("auth", Str()),
        Fld("firstName", Str()),
        Fld("gender", Str()),
        Fld("itemInSession", Str()),
        Fld("lastName", Str()),
        Fld("length", Dbl()),
        Fld("level", Str()),
        Fld("location", Str()),
        Fld("method", Str()),
        Fld("page", Str()),
        Fld("registration", Dbl()),
        Fld("sessionId", Str()),
        Fld("song", Str()),
        Fld("status", Str()),
        Fld("ts", Long()),
        Fld("userAgent", Str()),
        Fld("userId", Str())
    ])
    return log_schema


def test_parquet_tables(spark, output_data):
    """ Print first 5 rows of each table from S3 bucket
     Args:
        spark: spark session object
        output_data: location of S3 bucket for output data
    """
    songplays_table = spark.read.parquet(output_data + "songplays.parquet")
    users_table = spark.read.parquet(output_data + "users.parquet")
    songs_table = spark.read.parquet(output_data + "songs.parquet")
    artists_table = spark.read.parquet(output_data + "artists.parquet")
    time_table = spark.read.parquet(output_data + "time.parquet")
    print('Songplays Table:')
    print(songplays_table.show(n=5))
    print('Users Table:')
    print(users_table.show(n=5))
    print('Songs Table:')
    print(songs_table.show(n=5))
    print('Artists Table:')
    print(artists_table.show(n=5))
    print('Time Table:')
    print(time_table.show(n=5))


def main():
    start_time = time.time()
    spark = create_spark_session()
    input_data = "s3a://udacity-dend/"
    output_data = "s3a://sparkify-data-lake-output/"

    process_song_data(spark, input_data, output_data)
    process_log_data(spark, input_data, output_data)
    test_parquet_tables(spark, output_data)

    print("Execution Time: %s seconds" % int((time.time() - start_time)))


if __name__ == "__main__":
    main()
