# Maintainer: demostanis <demostanis@gmail.com>
pkgname=carrefour-api
pkgver=1.1.3
pkgrel=2
pkgdesc="HTTP API for remote shopping on carrefour.fr"
arch=('any')
url="https://github.com/demostanis/carrefour-api"
license=('MIT')
depends=('python-flask' 'python-requests')
source=('server.py' 'carrefour_api.py' 'carrefour_session.json' 'carrefour-api.service')
sha256sums=('dfd23c096f092e8c6f86c02ecf3170664447dd847b8504d5e6d85a082791237b'
            '440eac6f45b50451b4c02cb1db0e9e8ab2e2daf9ddadb900e688dc88f069c810'
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
