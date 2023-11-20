import os
import re
import json
import logging
import requests
import boto3
import psycopg2
from datetime import datetime
from psycopg2.sql import SQL, Identifier
from botocore.exceptions import ClientError
from bs4 import BeautifulSoup
from tabulate import tabulate

logger = logging.getLogger()
logger.setLevel(logging.INFO)
urls = [x.strip() for x in os.environ["WISHLIST_URLS"].split(',')]


def get_wishlist_items(amazon_url: str) -> list:
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"
    }
    session = requests.Session()
    response = session.get(url=amazon_url, headers=headers)
    content = response.text

    soup = BeautifulSoup(content, "html.parser")
    try:
        name = soup.find("span", id="profile-list-name").text
    except:
        logger.info("Something went wrong, can't find profile-list-name")
        logger.info(soup)
        return

    rows = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for i, span in enumerate(
        soup.find_all("li", {"data-itemid": re.compile(r"^[0-9A-Z]+$")})
    ):
        item_name = span.find("a", id=re.compile("itemName_.*"))["title"]
        requested = int(
            span.find("span", id=re.compile("itemRequested_.*")).text.strip()
        )
        purchased = int(
            span.find("span", id=re.compile("itemPurchased_.*")).text.strip()
        )
        rows.append(
            [
                timestamp,
                name,
                i + 1,
                span["data-itemid"],
                item_name,
                float(span["data-price"]) if "." in span["data-price"] else 0.0,
                requested,
                purchased,
                "YES" if requested == purchased else "NO",
            ]
        )

    return rows


def get_secret(secret_name: str, region_name: str) -> dict:
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    # Decrypts secret using the associated KMS key.
    secret = json.loads(get_secret_value_response["SecretString"])
    return secret


def insert_data_into_table(
    data: list,
    host: str,
    database: str,
    table: str,
    db_user: str,
    db_password: str,
    port: str = "5432",
):
    # query = SQL("INSERT INTO {} (list, num, item, item_name, price, requested, purchased, fulfilled) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);").format(Identifier(table))
    engine = psycopg2.connect(
        host=host,
        database=database,
        user=db_user,
        password=db_password,
        port=port,
    )

    cursor = engine.cursor()
    # cursor.executemany(query, data)
    cursor.executemany(
        SQL(
            "INSERT INTO {} (timestamp, list, num, item, item_name, price, requested, purchased, fulfilled) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);"
        ).format(Identifier(table)),
        data,
    )
    engine.commit()
    return


def handler(event, context):
    results = []

    for url in urls:
        # content = get(amazon_url=url)
        # result = parse(content=content)
        # results.append(result)
        result = get_wishlist_items(amazon_url=url)
        try:
            results.extend(result)
        except:
            logger.info("Empty Result, skipping...")

    secret_name = os.environ["SECRET_NAME"]
    region_name = os.environ["AWS_REGION"]
    database = os.environ["DATABASE_NAME"]
    table = os.environ["TABLE_NAME"]
    db_secret = get_secret(secret_name=secret_name, region_name=region_name)

    if len(results) == 0:
        logger.info("No results to insert")
        return {
            "statusCode": "200",  # a valid HTTP status code
            "body": "Lambda function invoked, but no data collected.",
        }

    insert_data_into_table(
        data=results,
        host=db_secret["host"],
        database=database,
        table=table,
        db_password=db_secret["password"],
        db_user=db_secret["username"],
        port=db_secret["port"],
    )

    content = tabulate(
        results,
        headers=[
            "list",
            "#",
            "item",
            "item_name",
            "price",
            "requested",
            "purchased",
            "fulfilled",
        ],
        tablefmt="pretty",
    )
    logger.info(content)
    # text_file=open("allresults121222.csv","w")
    # text_file.write(content)
    # text_file.close()

    return {
        "statusCode": "200",  # a valid HTTP status code
        "body": "Lambda function invoked",
    }


if __name__ == "__main__":
    handler(event="", context="")
