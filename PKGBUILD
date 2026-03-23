# Maintainer: demostanis <demostanis@gmail.com>
pkgname=carrefour-api
pkgver=1.0.0
pkgrel=1
pkgdesc="HTTP API for remote shopping on carrefour.fr"
arch=('any')
url="https://github.com/demostanis/carrefour-api"
license=('MIT')
depends=('python-flask' 'python-requests')
source=('server.py' 'carrefour_api.py' 'carrefour_session.json' 'carrefour-api.service')
sha256sums=('82d6751c32ebe179b05e33110f419da27cde283e468de4572469c74b782c2269'
            '61042533d831d7204db57732090dbb089d3208e61eea6936ba1670da779ce8cd'
            '861fa9ce0c371ca823dbd4c989e46809f02df52f226eae2ad3be55cda42fe22d'
            'a3a1b647e3b99e19dd990d54a5cb9341bef57b488e2563c7e6f949b59d0bda17')
install=carrefour-api.install

package() {
  # Install Python files
  install -Dm644 server.py "${pkgdir}/usr/share/carrefour-api/server.py"
  install -Dm644 carrefour_api.py "${pkgdir}/usr/share/carrefour-api/carrefour_api.py"
  
  # Install default session file for initial use
  install -Dm644 carrefour_session.json "${pkgdir}/usr/share/carrefour-api/carrefour_session.json"
  
  # Install systemd service
  install -Dm644 carrefour-api.service "${pkgdir}/usr/lib/systemd/system/carrefour-api.service"
}
