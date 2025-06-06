import httpx

def log_gps_stream(url="http://localhost:8000/gps/stream", log_file="gps_stream.log"):
    with httpx.stream("GET", url) as response:
        response.raise_for_status()
        with open(log_file, "a") as f:
            for line in response.iter_lines():
                if line:
                    f.write(line + "\n")
                    print(line)

if __name__ == "__main__":
    log_gps_stream()
    log_gps_stream()
