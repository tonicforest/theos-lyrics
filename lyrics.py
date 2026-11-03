import requests, re
class LyricsClient:
    API="https://lrclib.net/api/get"
    def fetch(self,title,artist,album=""):
        headers={"User-Agent":"TheosLyrics/0.1 (Linux desktop companion)"}
        params={"track_name":title,"artist_name":artist}
        if album:params["album_name"]=album
        try:
            r=requests.get(self.API,params=params,headers=headers,timeout=8)
            if r.status_code==404:
                r=requests.get("https://lrclib.net/api/search",
                    params={"track_name":title,"artist_name":artist},headers=headers,timeout=8)
                r.raise_for_status()
                for item in r.json():
                    if item.get("syncedLyrics"):return self.parse(item["syncedLyrics"])
                return []
            r.raise_for_status()
            lyrics=r.json().get("syncedLyrics")
            return self.parse(lyrics) if lyrics else []
        except Exception:return []
    @staticmethod
    def parse(text):
        out=[]
        for raw in (text or "").splitlines():
            stamps=re.findall(r"\[(\d{2}):(\d{2})(?:\.(\d{1,3}))?\]",raw)
            lyric=re.sub(r"\[(?:\d{2}):(?:\d{2})(?:\.\d{1,3})?\]","",raw).strip()
            for mm,ss,frac in stamps:
                out.append((int(mm)*60+int(ss)+(float("0."+frac) if frac else 0),lyric))
        return sorted(out)
