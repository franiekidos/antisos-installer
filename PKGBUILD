# Maintainer: Your Name <you@example.com>
pkgname=antisos-installer
pkgver=beta0.0.1
pkgrel=1
pkgdesc="AntisOS TUI installer"
arch=('x86_64')
url="https://example.com/antisos-installer"
license=('GPL')
depends=('python' 'python-textual' 'python-pygments' 'gparted')
source=("git+https://github.com/franiekidos/antisos-installer.git")
sha256sums=('SKIP')

package() {
    cd "$srcdir/antisos-installer"

    # Install main installer script
    install -Dm755 "installer" \
        "${pkgdir}/usr/bin/antisos-installer"

    # Install modular pages
    install -d "${pkgdir}/usr/share/antisos-installer/pages"
    cp -r pages/* "${pkgdir}/usr/share/antisos-installer/pages/"

    # Install CSS
    install -Dm644 "css/installer.tcss" \
        "${pkgdir}/usr/share/antisos-installer/css/installer.tcss"

    # Optional README
    install -Dm644 "README.md" \
        "${pkgdir}/usr/share/doc/antisos-installer/README.md"

    install -Dm644 "install.sh" \
        "${pkgdir}/usr/share/antisos-installer/install.sh"
}