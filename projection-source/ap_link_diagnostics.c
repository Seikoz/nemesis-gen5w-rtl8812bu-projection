#define _POSIX_C_SOURCE 200809L
#define _DEFAULT_SOURCE
#include <arpa/inet.h>
#include <errno.h>
#include <net/if.h>
#include <poll.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <time.h>
#include <unistd.h>

/* One bounded, interface-scoped mDNS probe. Never binds port 5353 or starts a daemon.
 * Legacy-unicast queries request replies to our ephemeral socket. No TXT contents,
 * phone names, instance names, hostnames, addresses or credentials are printed. */
static uint16_t u16(const unsigned char *p) { return (uint16_t)((p[0]<<8)|p[1]); }
static long long ms(void) {
    struct timespec t;
    if (clock_gettime(CLOCK_MONOTONIC, &t)) return 0;
    return (long long)t.tv_sec*1000+t.tv_nsec/1000000;
}
static int name(const unsigned char *p, size_t n, size_t *pos, char *out, size_t cap) {
    size_t i=*pos, used=0, next=0;
    unsigned steps=0;
    while (i<n && ++steps<=128) {
        unsigned c=p[i++];
        if (!c) { if (!next) next=i; out[used]=0; *pos=next; return 0; }
        if ((c&0xc0)==0xc0) {
            if (i>=n) return -1;
            if (!next) next=i+1;
            i=((c&0x3f)<<8)|p[i];
            continue;
        }
        if ((c&0xc0) || c>63 || i+c>n || used+c+1>=cap) return -1;
        if (used) out[used++]='.';
        while (c--) { unsigned char ch=p[i++]; out[used++]=(char)(ch>='A'&&ch<='Z'?ch+32:ch); }
    }
    return -1;
}
static const char *service(const char *s) {
    const char *p;
    if (!strcmp(s,"_airplay._tcp.local") ||
        ((p=strstr(s,"._airplay._tcp.local")) && !p[20])) return "_airplay._tcp";
    if (!strcmp(s,"_carplay-ctrl._tcp.local") ||
        ((p=strstr(s,"._carplay-ctrl._tcp.local")) && !p[25])) return "_carplay-ctrl._tcp";
    return NULL;
}
static unsigned record_lines;
static int decode(const unsigned char *p, size_t n, int family) {
    char owner[256], target[256];
    size_t pos=12;
    unsigned q, records, i;
    int matches=0;
    if (n<12 || !(p[2]&0x80)) return -1;
    q=u16(p+4); records=u16(p+6)+u16(p+8)+u16(p+10);
    if (q>32 || records>128) return -1;
    for (i=0;i<q;i++) {
        if (name(p,n,&pos,owner,sizeof(owner)) || pos+4>n) return -1;
        pos+=4;
    }
    for (i=0;i<records;i++) {
        unsigned type, len;
        size_t end, data;
        const char *s;
        if (name(p,n,&pos,owner,sizeof(owner)) || pos+10>n) return -1;
        type=u16(p+pos); len=u16(p+pos+8); pos+=10; data=pos; end=pos+len;
        if (end>n) return -1;
        s=service(owner);
        if (s && type==12) {
            size_t at=data;
            if (name(p,n,&at,target,sizeof(target)) || at>end) return -1;
            if (record_lines++<48) printf("mdns family=%d service=%s record=PTR ttl=%u\n",family,s,
                   (unsigned)((uint32_t)p[data-6]<<24|(uint32_t)p[data-5]<<16|(uint32_t)p[data-4]<<8|p[data-3]));
            matches++;
        } else if (s && type==33) {
            size_t at=data+6;
            if (len<7 || name(p,n,&at,target,sizeof(target)) || at>end) return -1;
            if (record_lines++<48) printf("mdns family=%d service=%s record=SRV port=%u\n",family,s,u16(p+data+4));
            matches++;
        } else if (s && type==16) {
            if (record_lines++<48) printf("mdns family=%d service=%s record=TXT contents=omitted\n",family,s);
            matches++;
        }
        pos=end;
    }
    return matches;
}
static size_t question(unsigned char *p, size_t pos, const char *s) {
    while (*s) {
        const char *e=strchr(s,'.');
        size_t n=e?(size_t)(e-s):strlen(s);
        p[pos++]=(unsigned char)n; memcpy(p+pos,s,n); pos+=n;
        s+=n; if (*s) s++;
    }
    p[pos++]=0; p[pos++]=0; p[pos++]=12; p[pos++]=0x80; p[pos++]=1;
    return pos;
}
static int open_probe(int family, unsigned index, const char *iface, const void *query, size_t len) {
    int fd=socket(family,SOCK_DGRAM,0), rc=-1;
    if (fd<0) return -1;
    if (setsockopt(fd,SOL_SOCKET,SO_BINDTODEVICE,iface,(socklen_t)(strlen(iface)+1))) goto fail;
    if (family==AF_INET) {
        struct ifreq req;
        struct sockaddr_in source, dst;
        memset(&req,0,sizeof(req)); strncpy(req.ifr_name,iface,IFNAMSIZ-1);
        if (ioctl(fd,SIOCGIFADDR,&req)) goto fail;
        source=*(struct sockaddr_in *)&req.ifr_addr; source.sin_port=0;
        if (bind(fd,(struct sockaddr *)&source,sizeof(source)) ||
            setsockopt(fd,IPPROTO_IP,IP_MULTICAST_IF,&source.sin_addr,sizeof(source.sin_addr))) goto fail;
        { unsigned char ttl=255;
          if (setsockopt(fd,IPPROTO_IP,IP_MULTICAST_TTL,&ttl,sizeof(ttl))) goto fail; }
        memset(&dst,0,sizeof(dst)); dst.sin_family=AF_INET; dst.sin_port=htons(5353);
        inet_pton(AF_INET,"224.0.0.251",&dst.sin_addr);
        rc=(int)sendto(fd,query,len,0,(struct sockaddr *)&dst,sizeof(dst));
    } else {
        struct sockaddr_in6 dst;
        int hops=255;
        if (setsockopt(fd,IPPROTO_IPV6,IPV6_MULTICAST_IF,&index,sizeof(index)) ||
            setsockopt(fd,IPPROTO_IPV6,IPV6_MULTICAST_HOPS,&hops,sizeof(hops))) goto fail;
        memset(&dst,0,sizeof(dst)); dst.sin6_family=AF_INET6; dst.sin6_port=htons(5353); dst.sin6_scope_id=index;
        inet_pton(AF_INET6,"ff02::fb",&dst.sin6_addr);
        rc=(int)sendto(fd,query,len,0,(struct sockaddr *)&dst,sizeof(dst));
    }
    if (rc==(int)len) return fd;
fail:
    { int saved=errno; close(fd); errno=saved; return -1; }
}
int main(int argc, char **argv) {
    unsigned char query[160]={0}, packet[4096];
    struct pollfd fds[2];
    unsigned index;
    size_t len;
    long long end;
    int i, packets=0, matches=0, malformed=0;
    if (argc==2 && !strcmp(argv[1],"--decode")) {
        size_t n=fread(packet,1,sizeof(packet),stdin);
        int rc=decode(packet,n,0);
        printf("decode=%s\n",rc<0?"malformed":"ok"); return rc<0?1:0;
    }
    if (argc!=1) return 2;
    index=if_nametoindex("rtwlan0");
    if (!index) { printf("mdns interface=rtwlan0 unavailable errno=%d\n",errno); return 1; }
    query[0]=0x4b;query[1]=0x50;query[5]=2;
    len=question(query,12,"_airplay._tcp.local");
    len=question(query,len,"_carplay-ctrl._tcp.local");
    for (i=0;i<2;i++) {
        fds[i].fd=open_probe(i?AF_INET6:AF_INET,index,"rtwlan0",query,len); fds[i].events=POLLIN;
        printf("mdns family=%d interface=rtwlan0 query=%s errno=%d\n",i?6:4,
               fds[i].fd<0?"failed":"sent",fds[i].fd<0?errno:0);
    }
    end=ms()+1200;
    while (packets<32 && ms()<end) {
        int remaining=(int)(end-ms()), rc;
        if (remaining<=0) break;
        rc=poll(fds,2,remaining);
        if (rc<=0) break;
        for (i=0;i<2 && packets<32;i++) if (fds[i].revents&POLLIN) {
            ssize_t n=recv(fds[i].fd,packet,sizeof(packet),0);
            if (n>0) { int found=decode(packet,(size_t)n,i?6:4); packets++;
                if (found<0) malformed++; else matches+=found; }
        }
    }
    for (i=0;i<2;i++) if (fds[i].fd>=0) close(fds[i].fd);
    printf("mdns packets=%d matched_records=%d malformed=%d window_ms=1200\n",packets,matches,malformed);
    puts("mdns no reply is inconclusive: multicast-only replies/firewall may hide discovery");
    return 0;
}
