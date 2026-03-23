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
sha256sums=('195668a7467e3bb2f9e190b475285876cfa896e66da075e19abd90abb4126850'
            '48931f3cf6175a8a02ab25ea02918a2c9e402cee92f06ff58d6ece70cdc00c67'
            '8667b8ecb73882fdd9432f8bcd7e255257186f2ca0e84df96a563f0d1f88be2e'
            '236268bb5c5071fd98c3684250d6f99e0a3f16de9d03b91743e84a6b5d62eb35')
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
