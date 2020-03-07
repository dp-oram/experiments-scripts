# Experiments

> Assumes Kalepso running locally on some port (e.g. 3306)

<details>
<summary>If Catalina compains about SSL...</summary>

```bash
/usr/bin/sudo /bin/mkdir -p /Applications/Xcode.app/Contents/Developer/Library/Frameworks/Python3.framework/Versions/3.7/etc
/usr/bin/sudo /bin/ln -s /etc/ssl/ /Applications/Xcode.app/Contents/Developer/Library/Frameworks/Python3.framework/Versions/3.7/etc/
sudo xcode-select -switch /
```

</details>
