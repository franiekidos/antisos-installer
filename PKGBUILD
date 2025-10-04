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
source=("git+https://github.com/franiekidos/antisos-installer.git")
sha256sums=('SKIP')  # replace with actual

# Optional: makepkg knows how to clone git repos automatically
# $srcdir/antisos-installer will exist after cloning

package() {
    cd "$srcdir/antisos-installer" || return

    # Make sure the installer file exists
    if [[ ! -f "installer" ]]; then
        echo "Error: 'installer' not found in the repository root"
        return 1
    fi

    # Install main installer script
    install -Dm755 "installer" "${pkgdir}/usr/bin/antisos-installer"

    # Optional: install any completion or configs if needed
    # mkdir -p "${pkgdir}/usr/share/antisos-installer"
    # cp -r configs "${pkgdir}/usr/share/antisos-installer/"
}