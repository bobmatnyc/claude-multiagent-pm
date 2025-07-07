# Deployment Configuration Updates

## mem0AI Service Location Change - M01-037

**Date**: 2025-07-07  
**Status**: ✅ COMPLETED  
**Impact**: DEPLOYMENT PATH CHANGE  

### Change Summary
The mem0AI service has been migrated from:
- **OLD**: `/Users/masa/Projects/managed/mem0ai/`
- **NEW**: `/Users/masa/Projects/Github/mem0ai/`

### Updated Deployment Commands

#### New Service Start Command:
```bash
cd /Users/masa/Projects/Github/mem0ai/server
source ../.venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8765 --reload
```

#### Previous Command (DEPRECATED):
```bash
cd /Users/masa/Projects/managed/mem0ai/server  # ❌ PATH NO LONGER EXISTS
source ../.venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8765 --reload
```

### Files Updated:
- ✅ `/Users/masa/Projects/Claude-PM/framework/LOCAL_SERVICES.md` - Updated deployment scripts
- ✅ `/Users/masa/Projects/Claude-PM/logs/health-report.json` - Updated monitoring paths

### Verification Steps:
1. ✅ Virtual environment intact at new location
2. ✅ Server files accessible (`main.py`, `requirements.txt`)
3. ✅ Port 8765 configuration unchanged
4. ✅ Service dependencies unchanged

### Action Required by Ops Agents:
- 🔄 **Update any manual deployment scripts** to use new path
- 🔄 **Update monitoring/alerting** to reference new location
- 🔄 **Verify service restart procedures** use correct path
- 📝 **Note**: Service port (8765) and startup command remain the same

---

*For questions, reference M01-037 in `/Users/masa/Projects/Claude-PM/trackdown/BACKLOG.md`*