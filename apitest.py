import urlutil

if __name__ == "__main__":

	url = "http://gis.kinatomic.com/POIware/api"
	postData = ""

	body, header = urlutil.Post(url, postData)
	assert urlutil.HeaderResponseCode(header) == "HTTP/1.1 400 Bad Request"

	postData = "action=query"
	body, header = urlutil.Post(url, postData)
	assert urlutil.HeaderResponseCode(header) == "HTTP/1.1 400 Bad Request"
	print body

	postData = "action=query&lat=51.&lon=0."
	body, header = urlutil.Post(url, postData)
	assert urlutil.HeaderResponseCode(header) == "HTTP/1.1 200 OK"
	#print body

	postData = "action=get"
	body, header = urlutil.Post(url, postData)
	assert urlutil.HeaderResponseCode(header) == "HTTP/1.1 400 Bad Request"
	#print body
	
	postData = "action=get&poiid=-1"
	body, header = urlutil.Post(url, postData)
	assert urlutil.HeaderResponseCode(header) == "HTTP/1.1 404 Not found"
	#print body

	postData = "action=get&poiid=1"
	body, header = urlutil.Post(url, postData)
	#assert urlutil.HeaderResponseCode(header) == "HTTP/1.1 404 Not found"
	#print body

	postData = "action=get&poiid=483,665,783,872,891,926,1003,1344,1621,1784,2069,2159"
	body, header = urlutil.Post(url, postData)
	print body
