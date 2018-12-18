import ipaddress

from mreg.models import Cname, Host, Srv, Zone
from mreg.utils import idna_encode

class ZoneFile(object):
    def __init__(self, zone):
        if zone.name.endswith('.in-addr.arpa'):
            self.zonetype = IPv4ReverseFile(zone)
        elif zone.name.endswith('.ip6.arpa'):
            self.zonetype = IPv6ReverseFile(zone)
        else:
            self.zonetype = ForwardFile(zone)

    def generate(self):
        return self.zonetype.generate()

class ForwardFile(object):

    def __init__(self, zone):
        self.zone = zone
        self.glue_done = set()

    def host_data(self, host):
        data = ""
        for i in ('ipaddresses', 'naptrs', 'txts',):
            for j in getattr(host, i).all():
                data += j.zf_string(self.zone.name)
        # For entries where the host is the resource record
        for i in ('cnames', ):
            for j in getattr(host, i).filter(zone=self.zone):
                data += j.zf_string(self.zone.name)
        if host.hinfo is not None:
            data += host.hinfo.zf_string
        if host.loc:
            data += host.loc_string(self.zone.name)
        return data

    def get_glue(self, ns):
        """Returns glue for a nameserver. If already used return blank"""
        if ns in self.glue_done:
            return ""
        else:
            self.glue_done.add(ns)
        if not ns.endswith("." + self.zone.name):
            return ""
        try:
            host = Host.objects.get(name=ns)
        except Host.DoesNotExist:
            #XXX: signal hostmaster?
            return "OPS: missing glue for %s\n" % ns
        if not host.ipaddresses.exists():
            #XXX: signal hostmaster?
            return "OPS: no ipaddress for name server %s\n" % ns
        # self's name servers do not need glue, as they will come later
        # in the zonefile.
        if host.zone == self.zone:
            return ""
        data = ""
        for ip in host.ipaddresses.all():
            data += ip.zf_string(self.zone.name)
        return data

    def get_subdomains(self):
        data = ""
        subzones = Zone.objects.filter(name__endswith="." + self.zone.name)
        for subzone in subzones.order_by('name'):
            for ns in subzone.nameservers.all():
                data += ns.zf_string(self.zone.name, subzone=subzone.name)
                data += self.get_glue(ns.name)
        if data:
            data = ';\n; Subdomains\n;\n' + data
        return data

    def generate(self):
        zone = self.zone
        # Print info about Zone and its nameservers
        data = zone.zf_string
        data += ';\n; Name servers\n;\n'
        for ns in zone.nameservers.all():
            data += ns.zf_string(zone.name)

        data += self.get_subdomains()
        try:
            root = Host.objects.get(name=zone.name)
            root_data = self.host_data(root)
            if root_data:
                data += ";\n"
                data +="@" + root_data
                data += ";\n"
        except Host.DoesNotExist:
            pass
        # Print info about hosts and their corresponding data
        data += ';\n; Host addresses\n;\n'
        hosts = Host.objects.filter(zone=zone.id).order_by('name')
        hosts = hosts.exclude(name=zone.name)
        for host in hosts:
            data += self.host_data(host)
        # Print misc entries
        data += ';\n; Services\n;\n'
        srvs = Srv.objects.filter(zone=zone.id)
        for srv in srvs:
            data += srv.zf_string(zone.name)
        data += ';\n; Cnames pointing out of the zone\n;\n'
        cnames = Cname.objects.filter(zone=zone.id).exclude(host__zone=zone.id)
        for cname in cnames:
            data += cname.zf_string(zone.name)
        return data


class IPv4ReverseFile(object):

    def __init__(self, zone):
        self.zone = zone

    def generate(self):
        zone = self.zone
        data = zone.zf_string
        data += ';\n; Name servers\n;\n'
        for ns in zone.nameservers.all():
            data += ns.zf_string(zone.name)
        # TODO: delegated entries, if any
        data += ';\n; Delegations \n;\n'
        _prev_net = 'z'
        for ip in zone.get_ipaddresses():
            rev = ipaddress.ip_address(ip.ipaddress).reverse_pointer
            # Add $ORIGIN between every new /24 found
            if not rev.endswith(_prev_net):
                _prev_net = rev[rev.find('.'):]
                data += "$ORIGIN {}.\n".format(_prev_net[1::])
            ptrip = rev[:rev.find('.')]
            data += "{}\tPTR\t{}.\n".format(ptrip, idna_encode(ip.host.name))
        return data


class IPv6ReverseFile(object):

    def generate(self, zone):
        data = zone.zf_string
        data += ';\n; Name servers\n;\n'
        for ns in zone.nameservers.all():
            data += ns.zf_string(zone.name)
        # TODO: delegated entries, if any
        data += ';\n; Delegations\n;\n'
        _prev_net = 'z'
        for ip in zone.get_ipaddresses():
            rev = ipaddress.ip_address(ip.ipaddress).reverse_pointer
            # Add $ORIGIN between every new /64 found
            if not rev.endswith(_prev_net):
                _prev_net = rev[32:]
                data += "$ORIGIN {}.\n".format(_prev_net)
            data += "{}\tPTR\t{}.\n".format(rev[:31], idna_encode(ip.host.name))
        return data
