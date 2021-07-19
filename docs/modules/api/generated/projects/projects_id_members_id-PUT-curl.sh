curl -X PUT \
  --header "Content-Type: application/json" \
  --data '{
             "project": 1,
             "user": 2,
             "role": "developer"
         }' \
  http://dtf.example.com/api/projects/1/members/1