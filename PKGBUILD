# Maintainer: Your Name <you@example.com>
pkgname=antisos-installer
pkgver=beta-0.0.1
pkgrel=1
pkgdesc="AntisOS TUI installer"
arch=('x86_64')
url="https://example.com/antisos-installer"
license=('GPL')
depends=('python' 'python-pip' 'python-textual' 'python-pygments' 'gparted')
source=("installer_core.py" "installer.py" "installer.tcss")
sha256sums=('SKIP' 'SKIP' 'SKIP')  # replace with actual checksums

package() {
    install -Dm755 "$srcdir/installer.py" "$pkgdir/usr/bin/antisos-installer"
    install -Dm644 "$srcdir/installer_core.py" "$pkgdir/usr/lib/antisos-installer/installer_core.py"
    install -Dm644 "$srcdir/installer.tcss" "$pkgdir/usr/lib/antisos-installer/installer.tcss"
}