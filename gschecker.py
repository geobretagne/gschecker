#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import urllib2
import os
import codecs
import urlparse
from jinja2 import Template
from inspirobot import Inspirobot
from lxml import etree
import datetime
import logging

cfg = {
    # 'proxy': '127.0.0.1:8888',
    'viewurlprefix': 'http://acme.org/geonetwork/apps/search/?uuid=',
    'xmlurlprefix': 'http://acme.org/geonetwork/srv/fre/xml_iso19139?uuid=',
    'cswurl': 'http://acme.org/geonetwork/srv/eng/csw-publication',
    'domain': 'acme.org',       # where is georchestra
    'username': 'x',            # an admin username
    'password': 'x',            # an admin password
    'usewms': True,
    'usewfs': True,
    'usewcs': True,
    'namespaces': [
        'ign',
        'geob_loc'
    ],
    'contact': {
        "organisationName": "acme",
        "email": "contact@acme.org",
        "url": "http://acme.org/"
    },
    'service_keywords': [
    ]
}


logging.basicConfig(level=logging.DEBUG)

cfgjson = 'gsconfig.json'
if not(os.path.isfile(cfgjson)):
    f=open(cfgjson, 'w')
    json.dump(cfg, f, indent=True)
    f.close()
cfg.update(json.load(open(cfgjson)))


# list all workspaces
# for each workspace, get wfs configuration
class Featuretype():

    def __init__(self, gs, json_href):
        self.gs = gs
        self.json_href = json_href
        self.json = self.gs.getjson(json_href)
        self.md = False
        self.mdUrl = False
        self.getMD()

    def getMD(self):
        """metadata resolver based on metadata links in GeoServer"""
        if self.json['featureType'].has_key('metadataLinks'):
            xmlmd = filter((lambda x: x['type']=='text/xml'), self.json['featureType']['metadataLinks']['metadataLink'])
            if len(xmlmd) > 0:
                #~ try:
                mdurl = xmlmd[0]['content']
                uxml = self.gs.getxml(mdurl).encode('utf8')
                xml = etree.tostring(etree.XML(uxml), encoding='UTF-8', xml_declaration=False)
                self.md = Inspirobot.MD(xml)
                self.mdUrl = urlparse.urljoin(cfg['xmlurlprefix'], self.md.fileIdentifier)
                logging.info('%s.%s : fileIdentifier %s' % (self.json['featureType']['namespace']['name'], self.json['featureType']['name'], self.md.fileIdentifier))
                return self.md
                #~ except:
                    #~ logging.error('%s.%s : can\'t resolve %s'%(self.json['featureType']['namespace']['name'], self.json['featureType']['name'], mdurl))
                    #~ return None
            else:
                logging.error('%s.%s : no metadataURL' % (self.json['featureType']['namespace']['name'], self.json['featureType']['name']))
                return None


class Coverage():

    def __init__(self, gs, json_href):
        self.gs = gs
        self.json_href = json_href
        self.json = self.gs.getjson(json_href)
        self.md = False
        self.mdUrl = False
        self.getMD()

    def getMD(self):
        """metadata resolver based on metadata links in GeoServer"""
        if self.json['coverage'].has_key('metadataLinks'):
            xmlmd = filter((lambda x: x['type']=='text/xml'), self.json['coverage']['metadataLinks']['metadataLink'])
            if len(xmlmd) > 0:
                #~ try:
                mdurl = xmlmd[0]['content']
                uxml = self.gs.getxml(mdurl).encode('utf8')
                xml = etree.tostring(etree.XML(uxml), encoding='UTF-8', xml_declaration=False)
                self.md = Inspirobot.MD(xml)
                self.mdUrl = urlparse.urljoin(cfg['xmlurlprefix'], self.md.fileIdentifier)
                logging.info('%s.%s : fileIdentifier %s' % (self.json['coverage']['namespace']['name'], self.json['coverage']['name'], self.md.fileIdentifier))
                return self.md
                #~ except:
                    #~ logging.error('%s.%s : can\'t resolve %s'%(self.json['featureType']['namespace']['name'], self.json['featureType']['name'], mdurl))
                    #~ return None
            else:
                logging.error('%s.%s : no metadataURL' % (self.json['coverage']['namespace']['name'], self.json['coverage']['name']))
                return None


class Workspace():

    def __init__(self, gs, name):
        self.gs = gs
        self.name = name
        self.featureTypes = []
        self.coverages = []
        self.wms_json = False
        self.wfs_json = False
        self.mditems = {
            'wms': {
                'success': False,
                'fileIdentifier' : '###wms.fileIdentifier###',
                'htmlUrl': '###wms.htmlUrl###',
                'xmlUrl': '###wms.xmlUrl###',
                'dateMD': '###wms.dateMD###',
                'dateCreation': '###wms.dateCreation###',
                'dateRevision': '###wms.dateRevision###',
                'getCapabilitiesUrl': '###wms.getCapabilitiesUrl###',
                'title': '###wms.title###',
                'abstract': '###wms.abstract###',
                'bbox': {
                    'minx': -180,
                    'miny': -90,
                    'maxx': 180,
                    'maxy': 90
                }
            },
            'wfs': {
                'success': False,
                'fileIdentifier' : '###wfs.fileIdentifier###',
                'htmlUrl': '###wfs.htmlUrl###',
                'xmlUrl': '###wfs.xmlUrl###',
                'dateMD': '###wfs.dateMD###',
                'dateCreation': '###wfs.dateCreation###',
                'dateRevision': '###wfs.dateRevision###',
                'getCapabilitiesUrl': '###wfs.getCapabilitiesUrl###',
                'title': '###wfs.title###',
                'abstract': '###wfs.abstract###',
                'bbox': {
                    'minx': -180,
                    'miny': -90,
                    'maxx': 180,
                    'maxy': 90
                }
            },
            'wcs': {
                'success': False,
                'fileIdentifier' : '###wfs.fileIdentifier###',
                'htmlUrl': '###wfs.htmlUrl###',
                'xmlUrl': '###wfs.xmlUrl###',
                'dateMD': '###wfs.dateMD###',
                'dateCreation': '###wfs.dateCreation###',
                'dateRevision': '###wfs.dateRevision###',
                'getCapabilitiesUrl': '###wfs.getCapabilitiesUrl###',
                'title': '###wfs.title###',
                'abstract': '###wfs.abstract###',
                'bbox': {
                    'minx': -180,
                    'miny': -90,
                    'maxx': 180,
                    'maxy': 90
                }
            },
            'featureTypes': [],
            'coverages': []
        }

        self.mditems['contact'] = cfg['contact']
        self.mditems['service_keywords'] = cfg['service_keywords']

        # get wms wfs wcs configuration
        try:
            url = 'services/wfs/workspaces/%s/settings.json?quietOnNotFound=1'%name
            self.wfs_json = self.gs.rest(url)
            logging.info('got WFS REST conf for %s', name)
        except Exception, err:
            logging.error("can't read wfs workspace %s, %s" % (self.name, err))

        try:
            self.wcs_json = self.gs.rest('services/wcs/workspaces/%s/settings.json?quietOnNotFound=1' % name)
            logging.info('got WCS REST conf for %s', name)
        except Exception, err:
            logging.error("cant' read wcs workspace %s, %s" % (self.name, err))

        try:
            url = 'services/wms/workspaces/%s/settings.json?quietOnNotFound=1' % name
            self.wms_json = self.gs.rest(url)
            logging.info('got WMS REST conf for %s', name)

        except Exception, err:
            logging.error("cant' read wms workspace %s, %s" % (self.name, err))

        try:
            # list featuretypes
            self.getFeaturetypes()
            # only featureTypes with associated metadata
            features = filter((lambda x: x.md), self.featureTypes)

            # list coverages
            self.getCoverages()
            # only coverages with associated metadata
            coverages = filter((lambda x: x.md), self.coverages)

            if len(features) > 0:
                for featureType in features:
                    self.mditems['featureTypes'].append(featureType)

                min_x_ft = min(map((lambda f: f.json['featureType']['latLonBoundingBox']['minx']), self.mditems['featureTypes']))
                min_y_ft = min(map((lambda f: f.json['featureType']['latLonBoundingBox']['miny']), self.mditems['featureTypes']))
                max_x_ft = min(map((lambda f: f.json['featureType']['latLonBoundingBox']['maxx']), self.mditems['featureTypes']))
                max_y_ft = min(map((lambda f: f.json['featureType']['latLonBoundingBox']['maxy']), self.mditems['featureTypes']))

                self.mditems['wfs']['fileIdentifier'] = cfg['fileIdentifierWfsFormat'].format(name=name)
                self.mditems['wfs']['htmlUrl'] = urlparse.urljoin(cfg['viewurlprefix'], self.mditems['wfs']['fileIdentifier'])
                self.mditems['wfs']['xmlUrl'] = urlparse.urljoin(cfg['xmlurlprefix'], self.mditems['wfs']['fileIdentifier'])
                self.mditems['wfs']['dateMD'] = datetime.datetime.now().strftime('%Y-%m-%d')
                self.mditems['wfs']['dateCreation'] = datetime.datetime.now().strftime('%Y-%m-%d')
                self.mditems['wfs']['dateRevision'] =   self.mditems['wfs']['dateCreation']
                self.mditems['wfs']['getCapabilitiesUrl'] = urlparse.urljoin('http://'+cfg['domain'], '/geoserver/'+name+'/wfs?SERVICE=WFS&amp;REQUEST=GetCapabilities&amp;')
                self.mditems['wfs']['title'] = self.wfs_json['wfs']['title']
                self.mditems['wfs']['abstract'] = self.wfs_json['wfs']['abstrct']
                self.mditems['wfs']['bbox']['minx'] = min_x_ft
                self.mditems['wfs']['bbox']['miny'] = min_y_ft
                self.mditems['wfs']['bbox']['maxx'] = max_x_ft
                self.mditems['wfs']['bbox']['maxy'] = max_y_ft

                self.mditems['wfs']['success'] = True

            if len(coverages) > 0:

                for coverage in coverages:
                    self.mditems['coverages'].append(coverage)

                min_x_cv = min(map((lambda f: f.json['coverage']['latLonBoundingBox']['minx']), self.mditems['coverages']))
                min_y_cv = min(map((lambda f: f.json['coverage']['latLonBoundingBox']['miny']), self.mditems['coverages']))
                max_x_cv = min(map((lambda f: f.json['coverage']['latLonBoundingBox']['maxx']), self.mditems['coverages']))
                max_y_cv = min(map((lambda f: f.json['coverage']['latLonBoundingBox']['maxy']), self.mditems['coverages']))

                self.mditems['wcs']['fileIdentifier'] = cfg['fileIdentifierWcsFormat'].format(name=name)
                self.mditems['wcs']['htmlUrl'] = urlparse.urljoin(cfg['viewurlprefix'], self.mditems['wcs']['fileIdentifier'])
                self.mditems['wcs']['xmlUrl'] = urlparse.urljoin(cfg['xmlurlprefix'], self.mditems['wcs']['fileIdentifier'])
                self.mditems['wcs']['dateMD'] = datetime.datetime.now().strftime('%Y-%m-%d')
                self.mditems['wcs']['dateCreation'] = datetime.datetime.now().strftime('%Y-%m-%d')
                self.mditems['wcs']['dateRevision'] =   self.mditems['wcs']['dateCreation']
                self.mditems['wcs']['getCapabilitiesUrl'] = urlparse.urljoin('http://'+cfg['domain'], '/geoserver/'+name+'/wcs?SERVICE=WCS&amp;REQUEST=GetCapabilities&amp;')
                self.mditems['wcs']['title'] = self.wcs_json['wcs']['title']
                self.mditems['wcs']['abstract'] = self.wcs_json['wcs']['abstrct']
                self.mditems['wcs']['bbox']['minx'] = min_x_cv
                self.mditems['wcs']['bbox']['miny'] = min_y_cv
                self.mditems['wcs']['bbox']['maxx'] = max_x_cv
                self.mditems['wcs']['bbox']['maxy'] = max_y_cv

                self.mditems['wcs']['success'] = True

            self.mditems['wms']['fileIdentifier'] = cfg['fileIdentifierWmsFormat'].format(name=name)
            self.mditems['wms']['htmlUrl'] = urlparse.urljoin(cfg['viewurlprefix'], self.mditems['wms']['fileIdentifier'])
            self.mditems['wms']['xmlUrl'] = urlparse.urljoin(cfg['xmlurlprefix'], self.mditems['wms']['fileIdentifier'])
            self.mditems['wms']['dateMD'] = datetime.datetime.now().strftime('%Y-%m-%d')
            self.mditems['wms']['dateCreation'] = datetime.datetime.now().strftime('%Y-%m-%d')
            self.mditems['wms']['dateRevision'] =   self.mditems['wms']['dateCreation']
            self.mditems['wms']['getCapabilitiesUrl'] = urlparse.urljoin('http://'+cfg['domain'], '/geoserver/'+name+'/wms?SERVICE=WMS&amp;REQUEST=GetCapabilities&amp;')
            self.mditems['wms']['title'] = self.wms_json['wms']['title']
            self.mditems['wms']['abstract'] = self.wms_json['wms']['abstrct']

            if len(coverages) == 0 and len(features) != 0:
                self.mditems['wms']['bbox']['minx'] = self.mditems['wfs']['bbox']['minx']
                self.mditems['wms']['bbox']['miny'] = self.mditems['wfs']['bbox']['miny']
                self.mditems['wms']['bbox']['maxx'] = self.mditems['wfs']['bbox']['maxx']
                self.mditems['wms']['bbox']['maxy'] = self.mditems['wfs']['bbox']['maxy']

            elif len(coverages) != 0 and len(features) == 0:
                self.mditems['wms']['bbox']['minx'] = self.mditems['wcs']['bbox']['minx']
                self.mditems['wms']['bbox']['miny'] = self.mditems['wcs']['bbox']['miny']
                self.mditems['wms']['bbox']['maxx'] = self.mditems['wcs']['bbox']['maxx']
                self.mditems['wms']['bbox']['maxy'] = self.mditems['wcs']['bbox']['maxy']

            elif len(coverages) != 0 and len(features) != 0:
                self.mditems['wms']['bbox']['minx'] = min(self.mditems['wcs']['bbox']['minx'], self.mditems['wfs']['bbox']['minx'])
                self.mditems['wms']['bbox']['miny'] = min(self.mditems['wcs']['bbox']['miny'], self.mditems['wfs']['bbox']['miny'])
                self.mditems['wms']['bbox']['maxx'] = max(self.mditems['wcs']['bbox']['maxx'], self.mditems['wfs']['bbox']['maxx'])
                self.mditems['wms']['bbox']['maxy'] = max(self.mditems['wcs']['bbox']['maxy'], self.mditems['wfs']['bbox']['maxy'])

            if len(coverages) + len(features) > 0:
                self.mditems['wms']['success'] = True

        except Exception, err:
            logging.error("can't read workspace %s, %s"%(self.name, err))

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name
                
    def getFeaturetypes(self):
        fts = self.gs.rest('workspaces'+'/'+self.name+'/featuretypes')['featureTypes']
        if fts:
            for ft in self.gs.rest('workspaces'+'/'+self.name+'/featuretypes')[u'featureTypes'][u'featureType']:
                self.featureTypes.append(Featuretype(self.gs, ft['href']))

    def getCoverages(self):
        cvs = self.gs.rest('workspaces'+'/'+self.name+'/coverages')['coverages']
        if cvs:
            for cv in self.gs.rest('workspaces'+'/'+self.name+'/coverages')[u'coverages'][u'coverage']:
                self.coverages.append(Coverage(self.gs, cv['href']))

    def getWFSMetadata(self):
        if self.mditems['wfs']['success'] == True:
            template = Template(codecs.open('mds_wfs.xml', 'r', 'utf-8').read())
            return template.render(self.mditems)
        else:
            return False

    def getWMSMetadata(self):
        if self.mditems['wms']['success'] == True:
            template = Template(codecs.open('mds_wms.xml', 'r', 'utf-8').read())
            return template.render(self.mditems)
        else:
            return False
            
    def getWCSMetadata(self):
        if self.mditems['wcs']['success'] == True:
            template = Template(codecs.open('mds_wcs.xml', 'r', 'utf-8').read())
            return template.render(self.mditems)
        else:
            return False
    
    def cswInsert(self, xmlmd):
        xml_insert = '''<?xml version="1.0" encoding="UTF-8"?>
<csw:Transaction service="CSW" version="2.0.2" xmlns:csw="http://www.opengis.net/cat/csw/2.0.2">
    <csw:Insert>
    %s
    </csw:Insert>
</csw:Transaction>'''%(xmlmd)


class GS():
    
    def __init__(self, domain, username, password):
        self.domain = domain
        self.username = username
        self.password = password

        if "proxy" in cfg:
            proxy_handler = urllib2.ProxyHandler({'http': cfg["proxy"]})
        else:
            proxy_handler = None

        passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
        passman.add_password(None, domain, username, password)
        pass_handler = urllib2.HTTPBasicAuthHandler(passman)

        if proxy_handler:
            self.admin_opener = urllib2.build_opener(proxy_handler, pass_handler)
        else:
            self.admin_opener = urllib2.build_opener(pass_handler)
        self.admin_opener.addheaders = [('Accept', 'application/json')]

    def __repr__(self):
        pass
        
    def __str__(self):
        pass
        
    def getxml(self, url):
        response = self.admin_opener.open(url)
        result = response.read().decode("UTF-8")
        response.close()
        return result
        
    def getjson(self, url):
        response = self.admin_opener.open(url)
        result = response.read().decode("UTF-8")
        response.close()
        return json.loads(result)

    def rest(self, restpath):
        url = urlparse.urljoin('http://'+self.domain, '/geoserver/rest/'+restpath)
        logging.debug("fetching %s"%url)
        response = self.admin_opener.open(url)
        result = response.read().decode("UTF-8")
        response.close()
        return json.loads(result)
        
    def postXML(self, url, xml):
        request = urllib2.Request(url, xml)
        request.add_header("Content-Type",'application/xml')
        request.get_method = lambda: "POST"
        try:
            conn = self.admin_opener.open(request)
        except urllib2.HTTPError,e:
            conn = e
        #~ # check. Substitute with appropriate HTTP code.
        if conn.code == 200:
            data = conn.read()
            print data
        else:
            print conn.code


geoserver = GS(cfg["domain"], cfg["username"], cfg["password"])
for namespace in cfg["namespaces"]:
    ws = Workspace(geoserver, namespace)

    xml = ws.getWFSMetadata()
    if (xml):
        xml_file_name = "{0}.wfs.xml".format(namespace)
        xml_file_path = os.path.join(u"results", xml_file_name)
        fmds = open(xml_file_path, 'w')
        fmds.write(xml.encode('utf8'))
        fmds.close()

    xml = ws.getWMSMetadata()
    if (xml):
        xml_file_name = "{0}.wms.xml".format(namespace)
        xml_file_path = os.path.join(u"results", xml_file_name)
        fmds = open(xml_file_path, 'w')
        fmds.write(xml.encode('utf8'))
        fmds.close()

    xml = ws.getWCSMetadata()
    if (xml):
        xml_file_name = "{0}.wcs.xml".format(namespace)
        xml_file_path = os.path.join(u"results", xml_file_name)
        fmds = open(xml_file_path, 'w')
        fmds.write(xml.encode('utf8'))
        fmds.close()
