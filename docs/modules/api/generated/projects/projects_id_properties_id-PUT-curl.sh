curl -X PUT \
  --header "Content-Type: application/json" \
  --data '{
             "project": 1,
             "name": "Branch",
             "required": false,
             "display": false,
             "display_as_link": false,
             "display_replace": "",
             "influence_reference": false
         }' \
  http://dtf.example.com/api/projects/1/properties/1