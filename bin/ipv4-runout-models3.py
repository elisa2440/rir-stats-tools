####
# ipv4_runout_models3
#
# Prediccion de agotamiento de ipv4 en fase 2 -- LACNIC
# (c) Elisa

## END

from numpy import *
from datetime import date
from datetime import timedelta
from datetime import datetime
from time import sleep
from time import mktime
from commons import getfile
import sys
import json
import commons.dprint
import getopt
commons.dprint.setAutoFlush()

def parseMongoDate(stringDate):
	b=stringDate[5:-1]
	c=[int(x) for x in b.split(",")]
	d=datetime(c[0],c[1]+1,c[2],c[3],c[4],c[5])
	timestamp=mktime(d.timetuple())
	return timestamp

hoy = date.today()
print hoy
fecha_fase2 = date(2014, 7, 1)
lastdays = (hoy - fecha_fase2).days
print lastdays 
dias_pred = 600
dash8 = pow(2,24)
# pool_reservado = pow(2,32-11)
pool_reservado = 0
ipv4libres_tmp = "tmp/reports_freespace.txt"


#fetch data
print "Fetching IPv4 allocation data...",
sys.stdout.flush()
serie_temporal = array([])
serie_temporal_corrida = array([])
serie_ipv4libres = array([])
serie_temporal_pred = []
serie_ipv4libres_pred = []

getfile.getfile("http://opendata.labs.lacnic.net/ipv4stats/ipv4avail/lacnic?lastdays=%s" % (lastdays-1), ipv4libres_tmp, 30)
print "done!"

print "Parsing JSON data...",
jsd_file = open(ipv4libres_tmp, "r")
datos = json.load(jsd_file)
jsd_file.close()
i = 0
for row in reversed(datos['rows']):
	ts=parseMongoDate(row['c'][0]['v'])
	serie_temporal = append(serie_temporal, ts)
	fip4 = row['c'][1]['v']
	serie_ipv4libres = append(serie_ipv4libres, fip4)
	i = i + 1
print "done!"


rango = xrange(1, lastdays+1)

for r in rango:
	fecha_ts2 = fecha_fase2 + timedelta(float(r))
	ts2 = mktime(fecha_ts2.timetuple())
	serie_temporal_corrida = append(serie_temporal_corrida, ts2)

print date.fromtimestamp(serie_temporal_corrida[0])
print date.fromtimestamp(serie_temporal_corrida[-1])
#print serie_temporal[0]

print "%s entries loaded." % (i)

#print serie_ipv4libres[0]
		
print "Corriendo modelos:"
print "-- "
runout_offsets = []
dash10_offsets = []

poly_degree = 2
try:
	opts, args = getopt.getopt(sys.argv[1:],"d:",["degree="])
	for o,a in opts:
		if o in ("-d", "--degree"):
			poly_degree = int(a)
except getopt.GetoptError:
	print './bin/ipv4_runout_models3.py -d <model_degree>'
	sys.exit(2)


model_poly = polyfit(serie_temporal, serie_ipv4libres, poly_degree)
print "Polynomial degree %s fitted successfully, result is: %s" % (poly_degree, model_poly)
	
base_t =int(amax(serie_temporal))
cero = int(amin(serie_temporal))

rango_pred = array([])	
rango_pred = append(rango_pred, serie_temporal_corrida)
for j in xrange(0,dias_pred):
	d = hoy + timedelta(j)
	ts = mktime(d.timetuple())
	rango_pred = append(rango_pred, ts)

time_series_future = xrange(0, len(rango_pred))
print time_series_future

fechas = []
for f in xrange(0, len(serie_temporal)):
	fechas.append(date.fromtimestamp(serie_temporal[f]))
	
serie_temporal_pred.append(array([]))
serie_ipv4libres_pred.append(array([]))

dash10_offset = -1
#f = open("html/pred_ipv4libres_%s.txt" % (str(hoy)), "w")
#g = open("tmp/vacios.txt", "w")
#f.write("Fecha,Modelo,Conocido,Limite\n")
for t in time_series_future:
	ipv4libres_estimado = polyval(model_poly, rango_pred[t])
	serie_ipv4libres_pred[-1] = append(serie_ipv4libres_pred[-1], ipv4libres_estimado)
	serie_temporal_pred[-1] = append(serie_temporal_pred[-1], rango_pred[t])
	#int_ipv4libres_estimado=int(round(ipv4libres_estimado))

	#if date.fromtimestamp(rango_pred[t]) in fechas:
	#	int_serie_ipv4libres=int(serie_ipv4libres[fechas.index(date.fromtimestamp(rango_pred[t]))])
	#	f.write(str(date.fromtimestamp(rango_pred[t]))+","+str(int_ipv4libres_estimado)+","+str(int_serie_ipv4libres)+","+"2097152\n")
	#else:
	#	f.write(str(date.fromtimestamp(rango_pred[t]))+","+str(ipv4libres_estimado)+","+","+"2097152\n")
		#g.write(str(date.fromtimestamp(rango_pred[t]))+"\n")
	
	print "t: %s, free_ipv4: %s" % (t, ipv4libres_estimado),
	if ipv4libres_estimado < 0.25*float(dash8) and dash10_offset == -1:
		dash10_offset =t-lastdays-1
	if ipv4libres_estimado < pool_reservado:
		break
	print '\r',
	sleep(0.005)
		
print " "
#print serie_ipv4libres_pred[0]
#f.close()

f = open("html/pred_ipv4libres_%s.txt" % (str(hoy)), "w")
#g = open("tmp/vacios.txt", "w")
f.write("Fecha,Modelo,Conocido,Limite\n")
for t in xrange(0, len(serie_ipv4libres_pred[0])-1):
	int_ipv4libres_estimado=int(round(serie_ipv4libres_pred[0][t]))
	if date.fromtimestamp(rango_pred[t]) in fechas:
		int_serie_ipv4libres=int(serie_ipv4libres[fechas.index(date.fromtimestamp(rango_pred[t]))])
		f.write(str(date.fromtimestamp(rango_pred[t]))+","+str(int_ipv4libres_estimado)+","+str(int_serie_ipv4libres)+","+str(pool_reservado)+"\n")
	else:
		f.write(str(date.fromtimestamp(rango_pred[t]))+","+str(int_ipv4libres_estimado)+","+","+str(pool_reservado)+"\n")
f.close()

a = open("html/fechas.json", "w")	
if t < lastdays - 1 + dias_pred - 1:
	#print "Delta T for dash10 global policy trigger was %s" % (dash10_offset)
	print "Delta T for dash11 runout is %s" % (t-lastdays-1)
	runout_offsets.append(t)
	dash10_offsets.append(dash10_offset)
	p3_date = date.fromtimestamp(rango_pred[t])
	print "Expected phase 3 entry date %s" % (p3_date)
	st = {'model-run-date':str(hoy), 'phase2-runout-date':str(p3_date)}
	dump = json.dumps(st)
	a.write(dump)
else:
	print "Delta T could not be identified, check for numerity instability"
	serie_temporal_pred.pop()
	serie_ipv4libres_pred.pop()
	
print "Calculating model error..."

largo = xrange(0, len(serie_temporal)-1)
media_ipv4libres = sum(serie_ipv4libres)/float(len(serie_temporal))
print media_ipv4libres
total = 0
residuo = 0

for i in largo:
	residuo = residuo + (serie_ipv4libres[i]-serie_ipv4libres_pred[0][i])**2
	total = total + (serie_ipv4libres[i]-media_ipv4libres)**2

print "%s, %s" % (residuo,total)
error2 = 1 - residuo/total
print "done!"
print "Error2 para modelo de grado %s es %s" % (poly_degree, error2)
		
print "--"		
	
