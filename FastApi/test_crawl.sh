#!/bin/bash
curl -X POST "http://crawler:8000/crawl" \
     -H "Content-Type: application/json" \
     -d '{
           "url": "https://gall.dcinside.com/mgallery/board/lists?id=stockus",
           "days": 1,
           "previous_days": 0
         }'