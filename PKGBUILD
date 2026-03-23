# Maintainer: demostanis <demostanis@gmail.com>
pkgname=carrefour-api
pkgver=1.1.3
pkgrel=1
pkgdesc="HTTP API for remote shopping on carrefour.fr"
arch=('any')
url="https://github.com/demostanis/carrefour-api"
license=('MIT')
depends=('python-flask' 'python-requests')
source=('server.py' 'carrefour_api.py' 'carrefour_session.json' 'carrefour-api.service')
sha256sums=('1aea61028050d2ac9efb3e775e3627296fe7343f30e2b5b7a487c8cce125c84a'
            'f8b01d438de8a564d36ac47f2fa950250913f2efc2477eb13b2610b09bbfa37d'
            '8667b8ecb73882fdd9432f8bcd7e255257186f2ca0e84df96a563f0d1f88be2e'
            '782b2dc2c168d0a27b94f760f65b5782bc9d98a9385446d5229d77a34d10995c')
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
