from payments.models import OwnerWallet, PlatformWallet

ow = OwnerWallet.get()
ow.balance = 0
ow.total_earned = 0
ow.save()

pw = PlatformWallet.get()
pw.balance = 0
pw.total_earned = 0
pw.save()

print(f"OwnerWallet reset: balance={ow.balance}, total_earned={ow.total_earned}")
print(f"PlatformWallet reset: balance={pw.balance}, total_earned={pw.total_earned}")
