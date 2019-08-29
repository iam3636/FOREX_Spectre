# Spectre Database (SDB)

## Setup

Head on over to AWS and hit

```
RDS -> create database -> easy create
```

This will give you the best practice settings. 

To make the database accessible outside the VPC group, you will want to click on the instance, hit the "Modify" button, make it publicly available and you may need to create a new security group  (for example we made one called "web_open") which allows for instances to be accessed through the internet only by a password.

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

- `MYSQL_USER`: click on the database name, go to the "Configuration" tab, in the table below there will be a column "Availability", and there will be an entry "Master Username"
- `MYSQL_PASSWORD`: click on the database name, go to the "Configuration" tab, in the table below there will be a column "Availability", and there will be an entry "Master Password". It may be "\****". What you will want to do is actually click on the particular instance, hit the "Modify" button, and set your own master password for that instance.
- `MYSQL_HOST_IP`: click on the instance, go to the "Connectivity & Security" tab, in the table below in the column "Endpoint & Port" will be an "Endpoint" address, it will look like a website address
- `MYSQL_PORT`: click on the instance, go to the "Connectivity & Security" tab, in the table below in the column "Endpoint & Port" will be a 4 digit port number
- `MYSQL_DATABASE`: click on the instance, go to the "Configuration" tab, in the table below in the column "Configurations" will be an entry named "DB instance id" 

## First Table

