source .env
yc serverless function create --name=myfunc
yc serverless function version create \
  --function-name=myfunc \
  --runtime python311 \
  --entrypoint index.main \
  --memory 512m \
  --execution-timeout 180s \
  --network-name	default\
  --source-path ./cloud_function \
  --environment DB_PORT=$NGROK_PORT,DB_HOST=$NGROK_HOST,DB_NAME=$DB_NAME,DB_USER=$DB_USER,DB_PASSWORD=$DB_PASSWORD,TOKEN=$GH_TOKEN
