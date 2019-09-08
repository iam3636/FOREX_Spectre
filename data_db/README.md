# Spectre Database (SDB)

## Setup

In order to setup the MYSQL DB, AWS has a [tutorial](https://aws.amazon.com/getting-started/tutorials/create-mysql-db). 

Head on over to AWS and hit

```
RDS -> create database -> MySQL
```

Choose your username and password

To make the database accessible outside the VPC group, you will want to click on the instance, hit the "Modify" button, make it publicly available and you may need to create a new security group  (for example we made one called "web_open") which allows for instances to be accessed through the internet only by a password. This allows connections to and from any IP address on ports 3305(MySQL), 22 (SSH), 80 (HTTP), and 443 (HTTPS) with the TCP protocol.

In order to setup the MYSQL engine to connect to your DB, AWS has a [tutorial](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_ConnectToInstance.html). 

Use a desktop application such as Sequel Pro to connect to the instance and instantiate a DB.

### Config file

You are going to want to save the credentials for your database in a `config.json` for programatic access; ensure that you do not push this to any public repository.

For the Spectre DB module we use the following format

```json
{"MYSQL_USER": {
	 "MYSQL_PASSWORD": ,
	 "MYSQL_HOST_IP": ,
   "MYSQL_PORT":,
   "MYSQL_DATABASE":}
}
```

You can find this info in AWS in the following manner

- `MYSQL_USER`: should have it from the setup, but if not click on the database name, go to the "Configuration" tab, in the table below there will be a column "Availability", and there will be an entry "Master Username"
- `MYSQL_PASSWORD`: should have it from the setup, but if not click on the database name, go to the "Configuration" tab, in the table below there will be a column "Availability", and there will be an entry "Master Password". It may be "\****". What you will want to do is actually click on the particular instance, hit the "Modify" button, and set your own master password for that instance.
- `MYSQL_HOST_IP`: click on the instance, go to the "Connectivity & Security" tab, in the table below in the column "Endpoint & Port" will be an "Endpoint" address, it will look like a website address
- `MYSQL_PORT`: click on the instance, go to the "Connectivity & Security" tab, in the table below in the column "Endpoint & Port" will be a 4 digit port number
- `MYSQL_DATABASE`: whatever you named using the desktop application.   

## First Table

Using the `sdb` package, and the `upload_df_to_db` function, any df that is uploaded to a non-existing table, is automatically given its own table.