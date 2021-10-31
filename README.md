# Price predictor

Prediction is based on provided percentile and data window this percentile is collected from.

Possible issues:
    
- Data loss while calculating prediction, if calculation time is greater than time between messages 
    from the order book are coming in. 