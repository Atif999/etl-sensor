CREATE TABLE raw_sensor_data (
    id SERIAL PRIMARY KEY,
    date TIMESTAMP NOT NULL,
    T FLOAT,            
    rh FLOAT,            
    p FLOAT,                        
    Tpot FLOAT,            
    Tdew FLOAT,          
    VPmax FLOAT,           
    VPact FLOAT,          
    VPdef FLOAT,           
    sh FLOAT,             
    H2OC FLOAT,           
    rho FLOAT,             
    wv FLOAT,              
    max_wv FLOAT,          
    wd FLOAT,              
    rain FLOAT,
	raining FLOAT,
    SWDR FLOAT,            
    PAR FLOAT,             
    max_PAR FLOAT,         
    Tlog FLOAT,           
    file_name VARCHAR(255),
    processed_at TIMESTAMP NOT NULL 
);

CREATE INDEX idx_raw_sensor_time ON raw_sensor_data (date);
CREATE INDEX idx_file_name ON raw_sensor_data (file_name);



CREATE TABLE aggregated_metrics (
    id SERIAL PRIMARY KEY,
    sensor_type VARCHAR(50) NOT NULL,
    min FLOAT,
    max FLOAT,
    mean FLOAT,
    std FLOAT,
	file_name VARCHAR(255),
    timestamp TIMESTAMP NOT NULL,
	processed_at TIMESTAMP NOT NULL
);
CREATE INDEX idx_sensor_type ON aggregated_metrics (sensor_type);