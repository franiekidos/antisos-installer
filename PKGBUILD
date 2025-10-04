# Maintainer: Antis
pkgname=antisos-installer
pkgver=test1.0.0
pkgrel=1
pkgdesc="Installer of AntisOS"
arch=('x86_64')
url="https://example.com"
license=('GPL')
depends=('bash' 'gum' 'git')  # common dependencies only
optdepends=('iwd: Choose for iwctl networking'
            'networkmanager: Choose for nmtui networking')
source=git+https://github.com/franiekidos/antisos-installer
sha256sums=('SKIP')  # replace with actual

package() {
    install -Dm755 "$srcdir/installer.sh" "$pkgdir/usr/bin/archminimal-installer"
}