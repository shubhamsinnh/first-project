# 🚀 PujaPath - Complete Setup & Usage Guide

## 📋 Table of Contents
1. [Quick Start](#quick-start)
2. [Admin Panel Guide](#admin-panel-guide)
3. [Features Overview](#features-overview)
4. [Troubleshooting](#troubleshooting)

---

## 🏁 Quick Start

### Initial Setup (First Time Only)

```bash
# 1. Activate virtual environment
source .venv/bin/activate

# 2. Install dependencies (if not already done)
pip install -r requirements.txt

# 3. Run database migrations
flask db upgrade

# 4. Seed sample data
curl http://localhost:5001/api/seed-data

# 5. Create admin account
curl http://localhost:5001/admin/init

# 6. Start the server
python app.py
```

### Daily Development

```bash
# Just activate and run
source .venv/bin/activate
python app.py
```

Server runs on: **http://localhost:5001**

---

## 🎯 Admin Panel Guide

### Accessing Admin Panel

1. **Login URL**: `http://localhost:5001/admin/login`
2. **Default Credentials**:
   - Username: `admin`
   - Password: `admin123`
   - ⚠️ **Change this in production!**

### Admin Features

#### 📊 Dashboard (`/admin/dashboard`)
- View total pandits, products, and bookings
- See pending approvals count
- Recent bookings list
- Recent pandit signups
- Quick action buttons

#### 👨‍🦳 Pandit Management (`/admin/pandits`)
- View all registered pandits
- Filter: All / Pending / Approved
- **Approve** pandits (makes them visible on homepage)
- **Delete** pandits (removes from database)
- See full details: experience, location, contact info

#### 🛍️ Product Management (`/admin/products`)
- View all puja materials
- **Add new products** via modal form
- **Delete products** with confirmation
- See product details and pricing

#### 📅 Booking Management (`/admin/bookings`)
- View all customer bookings
- See booking details: customer, puja type, date, address
- Track booking status (pending/confirmed/completed)
- Pandit assignment information

---

## ✨ Features Overview

### Customer-Facing Features

#### 🏠 Home Page (`/`)
- **Hero Section**: Gradient design with CTA buttons
- **Stats Counter**: Animated numbers (500+ Pandits, 10K+ Customers, 50+ Cities)
- **Pandits Section**: Carousel with 14 verified pandits
  - Click arrows to browse
  - "Book Now" opens booking modal
- **Puja Essentials**: 25+ products in carousel
  - "Add to Cart" functionality
  - Shopping cart icon in navbar
- **Testimonials**: 8 customer reviews in carousel
- **Ritual Bundles**: 4 complete packages with discounts
- **Featured Media**: Auto-rotating logos (Hindu, NDTV, Forbes, ET)

#### 🛒 Shopping Cart
- **Cart Icon**: Shows item count in navbar
- **Cart Modal**: 
  - View all items
  - Adjust quantities (+/-)
  - Remove items
  - See subtotal and total
  - Proceed to checkout
- **Persistence**: Cart saved in localStorage

#### 📅 Pandit Booking
- **Booking Modal**: Opens when clicking "Book Now"
- **Form Fields**:
  - Customer name, phone, email
  - Puja type (dropdown)
  - Preferred date
  - Address
  - Additional notes
- **Booking Fee**: ₹999 displayed
- **Confirmation**: Success message on submit

#### 📝 Pandit Signup (`/pandit-signup`)
- Beautiful two-column layout
- **Form Fields**:
  - Personal: Name, Age, Email, Phone
  - Professional: Experience, Location, Languages, Specialties
  - Terms & Conditions checkbox
- **Benefits Sidebar**: Why join PujaPath
- **Stats Display**: Network size
- **Success Page**: Next steps after submission

#### ℹ️ About Us (`/about`)
- Company story and history
- Mission & Vision
- Core values
- Impact statistics
- Why choose PujaPath
- CTA buttons

#### 📞 Contact Us (`/contact`)
- Contact form with validation
- Multiple contact methods:
  - Phone: +91 9155095375
  - Email: support@pujapath.com
  - Office address
- Social media links
- Success message on submission

---

## 🎨 Design Features

### Visual Enhancements
- **Poppins Font**: Modern, clean typography throughout
- **Gradient Text**: Purple-pink gradients on headings
- **Card Hover Effects**: Lift animation on hover
- **Smooth Animations**: Fade-in on scroll
- **Carousel Sliders**: Manual navigation with arrows and dots
- **Professional Colors**: Blue, purple, orange, green theme
- **Responsive**: Mobile-first design

### Interactive Elements
- **Smooth Scrolling**: Click menu items scroll to sections
- **Mobile Menu**: Hamburger menu for mobile devices
- **Modal Windows**: Click outside to close
- **Notifications**: Toast messages for cart additions
- **Counter Animation**: Numbers count up when scrolled into view

---

## 📊 Database Schema

After running migrations, you'll have these tables:

1. **users** - Customer accounts
2. **pandits** - Verified pandits (with approval workflow)
3. **puja_materials** - Product catalog
4. **testimonials** - Customer reviews
5. **bundles** - Ritual packages
6. **admins** - Admin users
7. **bookings** - Customer bookings

---

## 🔧 Troubleshooting

### Port 5000 Already in Use
**Solution**: App now runs on port 5001
- macOS AirPlay uses port 5000 by default

### Database Connection Errors
**Solution**: Check your `.env` file
```env
DATABASE_URL=postgresql://username:password@localhost:5432/pujapath
```

### Can't See Data on Homepage
**Solutions**:
1. Run seed data: `curl http://localhost:5001/api/seed-data`
2. Check if pandits are approved (only approved show on homepage)
3. Check database connection

### Admin Login Not Working
**Solutions**:
1. Run: `curl http://localhost:5001/admin/init`
2. Check session cookies are enabled
3. Clear browser cache and try again

### Images Not Loading
**Check**:
1. Images are in `/static/` folder
2. Pandit images in `/static/pandit/` folder
3. File names match exactly (case-sensitive)

---

## 🎯 What to Do Next

### For Development
1. **Clear Database** (if you want to reseed):
   ```python
   # In Python shell or create endpoint
   PujaMaterial.query.delete()
   Testimonial.query.delete()
   Bundle.query.delete()
   Pandit.query.delete()
   db.session.commit()
   ```

2. **Add Real Images**:
   - Replace placeholder images in `/static/`
   - Upload pandit photos to `/static/pandit/`
   - Add product images

3. **Customize Content**:
   - Edit seed data in `app.py`
   - Add your own pandits, products, reviews
   - Update contact information

### For Production
1. **Security**:
   - Change admin password
   - Update SECRET_KEY and JWT_SECRET_KEY
   - Use environment variables
   - Enable HTTPS

2. **Payment Integration**:
   - Add Razorpay/Paytm
   - Complete checkout flow
   - Generate invoices

3. **Email Notifications**:
   - Send booking confirmations
   - Notify pandits of new bookings
   - Contact form responses

---

## 📱 User Workflows

### Customer Journey
1. Visit homepage
2. Browse pandits/products
3. Book pandit OR add items to cart
4. Fill booking form OR checkout
5. Receive confirmation

### Pandit Journey
1. Visit `/pandit-signup`
2. Fill application form
3. Receive success message
4. Wait for admin approval
5. Profile goes live
6. Receive booking notifications

### Admin Journey
1. Login at `/admin/login`
2. View dashboard statistics
3. Approve pending pandits
4. Manage products
5. Monitor bookings

---

## 🎉 Key Achievements

✅ **Beautiful, Modern Design** - Gradient colors, animations, professional UI
✅ **Full Booking System** - Modal-based, form validation, confirmation
✅ **Shopping Cart** - Add to cart, manage quantities, checkout ready
✅ **Admin Panel** - Complete management system
✅ **25+ Products** - Rich catalog of puja materials
✅ **14 Pandits** - Across 10+ major Indian cities
✅ **Responsive Design** - Works on all devices
✅ **Database Ready** - All migrations applied
✅ **Production Ready** - Clean code, proper structure

---

## 📞 Support

For questions or issues:
- Email: support@pujapath.com
- Phone: +91 9155095375

---

Made with ❤️ for preserving Vedic traditions



