/** Маршруты сайта: главная, вход, заказы, профиль. */

import { useEffect } from 'react'
import { Route, Routes, useLocation } from 'react-router-dom'
import { AuthProvider } from './state/AuthContext'
import { CartProvider } from './state/CartContext'
import { ToastProvider } from './state/ToastContext'
import { Header } from './components/Header'
import { Footer } from './components/Footer'
import { CartDrawer } from './components/CartDrawer'
import { CartFab } from './components/CartFab'
import { AiFab } from './components/AiFab'
import HomePage from './pages/Home'
import AuthPage from './pages/AuthPage'
import OrdersPage from './pages/OrdersPage'
import ProfilePage from './pages/ProfilePage'

function ScrollToTop() {
  const { pathname } = useLocation()
  useEffect(() => {
    window.scrollTo(0, 0)
  }, [pathname])
  return null
}

export default function App() {
  return (
    <ToastProvider>
      <AuthProvider>
        <CartProvider>
          <ScrollToTop />
          <Header />
          <main id="top">
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/login" element={<AuthPage />} />
              <Route path="/orders" element={<OrdersPage />} />
              <Route path="/profile" element={<ProfilePage />} />
              <Route path="*" element={<HomePage />} />
            </Routes>
          </main>
          <Footer />
          <CartDrawer />
          <CartFab />
          <AiFab />
        </CartProvider>
      </AuthProvider>
    </ToastProvider>
  )
}
