curl -X PUT `
  --header "Content-Type: application/json" `
  --data '{
             ""name"": ""Demo Project New Name"",
             ""slug"": ""demo-project""
         }' `
  http://dtf.example.com/api/projects/1