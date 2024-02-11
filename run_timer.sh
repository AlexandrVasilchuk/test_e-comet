source .env
yc serverless trigger create timer \
  --name mytimer \
  --cron-expression '0 * ? * * *' \
  --invoke-function-id $FUNCTION_ID \
  --retry-attempts 1 \
  --retry-interval 10s