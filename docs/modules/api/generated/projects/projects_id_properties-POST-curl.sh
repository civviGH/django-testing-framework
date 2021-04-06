curl -X POST \
  --header "Content-Type: application/json" \
  --data '{
             "name": "Property Name",
             "required": false,
             "display": true,
             "display_as_link": false,
             "display_replace": "Value is {VALUE}",
             "influence_reference": false
         }' \
  http://dtf.example.com/api/projects/1/properties