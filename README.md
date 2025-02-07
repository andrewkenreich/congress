# Introduction

This backend utilizes data from <https://api.congress.gov/> and <https://www.federalregister.gov/developers/documentation/api/v1> to create a custom backend in OpenBB Workspace

To use this backend, you will need to first get a key from <https://api.congress.gov/sign-up/> - federal register is free.

The key can be added to the .env file as `CONGRESS_API_KEY`.

## Step 1 - Run the backend

One you have your data in the folder you can run the backend with :

```python
pip install -r requirements.txt
```

```python
Run `uvicorn main:app --port 5051`
```

## Step 2 - Add to OpenBB Workspace - <https://pro.openbb.co/app/data-connectors>

Now you can add the backend to the [data connectors page](https://pro.openbb.co/app/data-connectors) with the base url of your API. In this case it is `http://localhost:5051`

## Step 3 - Once Added you can navigate to the `Templates` page and add the `Congressional Data & Executive Orders` template

This template includes data from the Congressional API and the Federal Register API to provide a comprehensive view of Congressional data and Executive Orders.

You can customize the template to your needs by editing the `templates.json` file.

