curl -X POST `
  --header "Content-Type: application/json" `
  --data '{
             ""user"": 1,
             ""role"": ""developer""
         }' `
  http://dtf.example.com/api/projects/1/members