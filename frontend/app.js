const API = "http://127.0.0.1:8000";

const S = { thuCung: [], thietBi: [], canhBao: [], chon: null };

const $ = (id) => document.getElementById(id);
const ngu = (ms) => new Promise((xong) => setTimeout(xong, ms));
const gio = (t) => new Date(t).toLocaleString("vi-VN");

const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

const TEN_CB = {
    THUC_AN_THAP: "Thức ăn sắp hết",
    HET_THUC_AN: "Đã hết thức ăn, hãy nạp thêm",
    NUOC_THAP: "Nước sắp hết",
    MAT_KET_NOI: "Thiết bị mất kết nối",
};

const TEN_TT = { THANH_CONG: "Thành công", THAT_BAI: "Thất bại", CHO_XU_LY: "Đang chờ", HET_HAN: "Hết hạn" };

async function goiApi(duongDan, tuyChon = {}) {
    const token = localStorage.getItem("token");
    const tieuDe = { ...(tuyChon.headers || {}) };

    if (token) {
        tieuDe.Authorization = "Bearer " + token;
    }

    const res = await fetch(API + duongDan, { ...tuyChon, headers: tieuDe });

    if (res.status === 401 && token) {
        dangXuat();
        throw new Error("Phiên đăng nhập đã hết hạn.");
    }

    if (!res.ok) {
        const loi = await res.json().catch(() => ({}));
        throw new Error(typeof loi.detail === "string" ? loi.detail : "Có lỗi xảy ra");
    }

    return res.json();
}

const gui = (method, body) => ({
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
});

// ---------- Tiện ích hiển thị ----------

function tuoi(ngaySinh) {
    if (!ngaySinh) return "";
    const thang = (Date.now() - new Date(ngaySinh)) / 2629800000;
    return thang >= 12 ? Math.floor(thang / 12) + " tuổi" : Math.max(1, Math.floor(thang)) + " tháng";
}

function thongTin(tc) {
    return [tc.loai, tuoi(tc.ngay_sinh), tc.can_nang ? tc.can_nang + " kg" : ""]
        .filter(Boolean).join(" · ");
}

function bieuTuong(tc) {
    const loai = String(tc.loai || "").toLowerCase();
    return /ch[oó]|dog/.test(loai) ? "🐶" : /m[eè]o|cat/.test(loai) ? "🐱" : "🐾";
}

function anh(tc) {
    if (tc.anh) {
        const nguon = tc.anh.startsWith("/") ? API + tc.anh : tc.anh;

        return `<img class="anh" src="${esc(nguon)}" alt=""
            onerror="this.outerHTML='<div class=anh>${bieuTuong(tc)}</div>'">`;
    }

    return `<div class="anh">${bieuTuong(tc)}</div>`;
}

const tcChon = () => S.thuCung.find((t) => t.ma_thu_cung === S.chon);

// Thiết bị của bé = thiết bị cùng chủ
const thietBiCua = (tc) =>
    S.thietBi.find((t) => tc && t.ma_nguoi_dung === tc.ma_nguoi_dung) || S.thietBi[0];

const dangOnline = (tb) => tb && tb.trang_thai === "DANG_KET_NOI";

// ---------- Màn hình danh sách ----------

function veDanhSach() {
    const khung = $("ds-thu-cung");

    if (!S.thuCung.length) {
        khung.textContent = "Chưa có thú cưng nào.";
        return;
    }

    khung.innerHTML = S.thuCung.map((tc) => {
        const on = dangOnline(thietBiCua(tc));

        return `<article class="the-be">
            ${anh(tc)}
            <div class="the-be-nd">
                <h3>${esc(tc.ten_thu_cung)}</h3>
                <p class="phu">${esc(thongTin(tc))}</p>
                <p class="${on ? "ok" : "mat"}">${on ? "✓ Máy cho ăn đang kết nối" : "✕ Máy mất kết nối"}</p>
                <button class="nut-xanh" onclick="moChiTiet(${tc.ma_thu_cung})">
                    Cho ${esc(tc.ten_thu_cung)} ăn
                </button>
            </div>
        </article>`;
    }).join("");
}

// ---------- Màn hình chi tiết ----------

function moChiTiet(ma) {
    S.chon = ma;
    const tc = tcChon();

    $("man-ds").hidden = true;
    $("man-ct").hidden = false;
    window.scrollTo(0, 0);

    $("ct-be").innerHTML = `<div class="the-be">${anh(tc)}
        <div class="the-be-nd">
            <h3>${esc(tc.ten_thu_cung)}</h3>
            <p class="phu">${esc(thongTin(tc))}</p>
            <p class="phu">Giống: ${esc(tc.giong || "Chưa cập nhật")}</p>
            <p class="phu">Giới tính: ${esc(tc.gioi_tinh || "Chưa cập nhật")}</p>
        </div></div>`;

    $("nut-cho-an").textContent = "Cho " + tc.ten_thu_cung + " ăn";
    $("kq-cho-an").textContent = "";
    $("kq-lich").textContent = "";

    veMay();
    taiLich().catch(console.error);
    taiLichSu().catch(console.error);
}

function veDanhSachLai() {
    S.chon = null;
    $("man-ct").hidden = true;
    $("man-ds").hidden = false;
    veDanhSach();
}

function thanh(ten, muc, loai, nguong) {
    return `<div class="muc">
        <div class="hang gian"><span>${ten}</span><b>${Math.round(muc)}%</b></div>
        <div class="ray"><div class="thanh ${loai} ${muc < nguong ? "thap" : ""}" style="width:${muc}%"></div></div>
    </div>`;
}

function veMay() {
    const tb = thietBiCua(tcChon());

    if (!tb) {
        $("ct-may").textContent = "Chưa có thiết bị.";
        return;
    }

    const on = dangOnline(tb);

    $("ct-may").innerHTML = `
        <div class="hang gian">
            <b>${esc(tb.ten_thiet_bi)}</b>
            <span class="nhan ${on ? "on" : "off"}">${on ? "Đang kết nối" : "Mất kết nối"}</span>
        </div>
        ${thanh("🍚 Thức ăn", tb.muc_thuc_an, "thuc-an", 50)}
        ${thanh("💧 Nước", tb.muc_nuoc, "nuoc", 20)}`;
}

async function choAn() {
    const tc = tcChon();
    const tb = thietBiCua(tc);
    const kq = $("kq-cho-an");
    const nut = $("nut-cho-an");
    const gam = Number($("luong").value);

    if (!tb) { kq.textContent = "Chưa có thiết bị."; return; }
    if (gam <= 0) { kq.textContent = "Lượng thức ăn phải lớn hơn 0."; return; }

    nut.disabled = true;
    kq.textContent = "Đang gửi lệnh...";

    try {
        const lenh = await goiApi("/api/cho-an-ngay", gui("POST", {
            ma_thu_cung: tc.ma_thu_cung,
            ma_thiet_bi: tb.ma_thiet_bi,
            luong_thuc_an: gam,
        }));

        kq.textContent = "⏳ Đã gửi lệnh, đang chờ máy cho ăn...";

        let tt = "CHO_XU_LY";

        for (let i = 0; i < 16 && tt === "CHO_XU_LY"; i++) {
            await ngu(2000);
            tt = (await goiApi("/api/lich-su-cho-an/" + lenh.ma_lich_su)).trang_thai;
        }

        kq.textContent = {
            THANH_CONG: "✅ Máy đã cho " + tc.ten_thu_cung + " ăn xong.",
            THAT_BAI: "❌ Cho ăn thất bại (thiếu thức ăn hoặc mất kết nối).",
        }[tt] || "⌛ Máy không phản hồi, lệnh đã hết hạn.";

        await lamMoi();
    } catch (loi) {
        kq.textContent = "❌ " + loi.message;
    } finally {
        nut.disabled = false;
    }
}

// ---------- Lịch cho ăn ----------

async function taiLich() {
    const ds = (await goiApi("/api/lich-cho-an"))
        .filter((l) => l.ma_thu_cung === S.chon)
        .sort((a, b) => a.gio_cho_an.localeCompare(b.gio_cho_an));

    $("ds-lich").innerHTML = ds.length ? ds.map((l) => `
        <div class="dong ${l.dang_hoat_dong ? "" : "tat"}">
            <b class="gio">${esc(l.gio_cho_an)}</b>
            <span class="phu">${l.luong_thuc_an}g mỗi lần</span>
            <span class="nhom-nut">
                <button class="nut-nho" onclick="batTat(${l.ma_lich}, ${!l.dang_hoat_dong})">${l.dang_hoat_dong ? "Tắt" : "Bật"}</button>
                <button class="nut-nho xoa" onclick="xoaLich(${l.ma_lich})">Xóa</button>
            </span>
        </div>`).join("") : '<p class="phu">Chưa có lịch cho bé.</p>';
}

async function themLich() {
    const tc = tcChon();
    const tb = thietBiCua(tc);
    const kq = $("kq-lich");
    const h = $("gio-lich").value;
    const gam = Number($("luong-lich").value);

    if (!h) { kq.textContent = "Hãy chọn giờ cho ăn."; return; }
    if (gam <= 0) { kq.textContent = "Lượng thức ăn phải lớn hơn 0."; return; }
    if (!tb) { kq.textContent = "Chưa có thiết bị."; return; }

    try {
        await goiApi("/api/lich-cho-an", gui("POST", {
            ma_thu_cung: tc.ma_thu_cung,
            ma_thiet_bi: tb.ma_thiet_bi,
            gio_cho_an: h,
            luong_thuc_an: gam,
            dang_hoat_dong: true,
        }));

        kq.textContent = "✅ Đã thêm lịch " + h + ".";
        await taiLich();
    } catch (loi) {
        kq.textContent = "❌ " + loi.message;
    }
}

async function batTat(ma, bat) {
    try {
        await goiApi("/api/lich-cho-an/" + ma, gui("PUT", { dang_hoat_dong: bat }));
        await taiLich();
    } catch (loi) {
        alert("Không thể cập nhật lịch: " + loi.message);
    }
}

async function xoaLich(ma) {
    if (!confirm("Xóa lịch cho ăn này?")) return;

    try {
        await goiApi("/api/lich-cho-an/" + ma, { method: "DELETE" });
        await taiLich();
    } catch (loi) {
        alert("Không thể xóa lịch: " + loi.message);
    }
}

// ---------- Lịch sử ----------

async function taiLichSu() {
    const ds = (await goiApi("/api/lich-su-cho-an"))
        .filter((h) => h.ma_thu_cung === S.chon)
        .slice(0, 10);

    $("ds-su").innerHTML = ds.length ? ds.map((h) => `
        <div class="dong">
            <b>🍚 ${h.luong_thuc_an}g</b>
            <span class="nhan ${h.trang_thai}">${TEN_TT[h.trang_thai] || h.trang_thai}</span>
            <span class="phu">${h.hinh_thuc === "TU_DONG" ? "Tự động" : "Thủ công"} · ${gio(h.thoi_gian_cho_an)}</span>
        </div>`).join("") : '<p class="phu">Chưa có lần cho ăn nào.</p>';
}

// ---------- Chuông cảnh báo ----------

function veChuong() {
    const chuaDoc = S.canhBao.filter((c) => !c.da_doc).length;
    const huy = $("so-canh-bao");

    huy.hidden = chuaDoc === 0;
    huy.textContent = chuaDoc;

    $("ds-canh-bao").innerHTML = S.canhBao.length ? S.canhBao.slice(0, 30).map((c) => `
        <div class="canh-bao ${c.da_doc ? "da-doc" : ""}">
            <b>⚠️ ${esc(TEN_CB[c.loai_canh_bao] || c.noi_dung)}</b>
            <span class="phu">${gio(c.thoi_gian_tao)}</span>
            ${c.da_doc ? "" : `<button class="nut-nho" onclick="daDoc(${c.ma_canh_bao})">Đã đọc</button>`}
        </div>`).join("") : '<p class="phu">Không có cảnh báo.</p>';
}

function moCanhBao() {
    $("tam-cb").hidden = false;
}

async function daDoc(ma) {
    try {
        await goiApi("/api/canh-bao/" + ma + "/da-doc", { method: "PUT" });
        S.canhBao = await goiApi("/api/canh-bao");
        veChuong();
    } catch (loi) {
        alert("Không thể cập nhật cảnh báo: " + loi.message);
    }
}

// ---------- Thêm thú cưng ----------

function moThemBe() {
    $("kq-them-be").textContent = "";
    $("tam-them").hidden = false;
}

async function themBe() {
    const kq = $("kq-them-be");
    const ten = $("be-ten").value.trim();
    const canNang = $("be-can-nang").value;

    if (!ten) {
        kq.textContent = "Hãy nhập tên bé.";
        return;
    }

    // Chưa có đăng nhập: gắn bé cho chủ của thiết bị đầu tiên
    if (!S.thietBi.length) {
        kq.textContent = "Chưa có thiết bị nào để gắn bé vào. Hãy thêm thiết bị trước.";
        return;
    }

    try {
        await goiApi("/api/thu-cung", gui("POST", {
            ma_nguoi_dung: S.thietBi[0].ma_nguoi_dung,
            ten_thu_cung: ten,
            loai: $("be-loai").value,
            giong: $("be-giong").value.trim() || null,
            gioi_tinh: $("be-gioi-tinh").value || null,
            ngay_sinh: $("be-ngay-sinh").value || null,
            can_nang: canNang ? Number(canNang) : null,
            anh: $("be-anh").value.trim() || null,
        }));

        ["be-ten", "be-giong", "be-ngay-sinh", "be-can-nang", "be-anh"]
            .forEach((id) => { $(id).value = ""; });

        $("tam-them").hidden = true;

        await lamMoi();
    } catch (loi) {
        kq.textContent = "❌ " + loi.message;
    }
}

// ---------- Đăng nhập / đăng xuất ----------

let cheDoDangKy = false;

function hienDangNhap() {
    S.chon = null;
    $("man-ds").hidden = true;
    $("man-ct").hidden = true;
    $("man-dn").hidden = false;
    $("chuong").hidden = true;
    $("nut-thoat").hidden = true;
}

function hienUngDung() {
    $("man-dn").hidden = true;
    $("man-ds").hidden = false;
    $("chuong").hidden = false;
    $("nut-thoat").hidden = false;
}

function dangXuat() {
    localStorage.removeItem("token");
    S.thuCung = [];
    S.thietBi = [];
    S.canhBao = [];
    hienDangNhap();
}

function hoiDangXuat() {
    if (confirm("Bạn có chắc chắn muốn đăng xuất không?")) {
        dangXuat();
    }
}

function doiCheDo() {
    cheDoDangKy = !cheDoDangKy;

    $("dn-nhan-ten").hidden = !cheDoDangKy;
    $("nut-dn").textContent = cheDoDangKy ? "Đăng ký" : "Đăng nhập";
    $("nut-doi-che-do").textContent = cheDoDangKy
        ? "Đã có tài khoản? Đăng nhập"
        : "Chưa có tài khoản? Đăng ký";
    $("kq-dn").textContent = "";
}

async function guiDangNhap() {
    const kq = $("kq-dn");
    const email = $("dn-email").value.trim();
    const matKhau = $("dn-mat-khau").value;

    if (!email || !matKhau) {
        kq.textContent = "Hãy nhập email và mật khẩu.";
        return;
    }

    localStorage.removeItem("token");

    try {
        if (cheDoDangKy) {
            await goiApi("/api/dang-ky", gui("POST", {
                ho_ten: $("dn-ho-ten").value.trim() || email,
                email: email,
                mat_khau: matKhau,
            }));
        }

        const ketQua = await goiApi("/api/dang-nhap", gui("POST", {
            email: email,
            mat_khau: matKhau,
        }));

        localStorage.setItem("token", ketQua.access_token);

        $("dn-mat-khau").value = "";
        kq.textContent = "";

        hienUngDung();
        await lamMoi();
    } catch (loi) {
        kq.textContent = "❌ " + loi.message;
    }
}

// ---------- Tải dữ liệu và tự làm mới ----------

async function lamMoi() {
    [S.thuCung, S.thietBi, S.canhBao] = await Promise.all([
        goiApi("/api/thu-cung"),
        goiApi("/api/thiet-bi"),
        goiApi("/api/canh-bao"),
    ]);

    veChuong();

    if (S.chon) {
        veMay();
        await taiLichSu();
    } else {
        veDanhSach();
    }
}

if (localStorage.getItem("token")) {
    hienUngDung();

    lamMoi().catch(() => {
        $("ds-thu-cung").textContent =
            "Không kết nối được máy chủ. Hãy chạy backend rồi tải lại trang.";
    });
} else {
    hienDangNhap();
}

setInterval(() => {
    if (localStorage.getItem("token")) {
        lamMoi().catch(() => {});
    }
}, 5000);