"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  ArrowUpRight, 
  ArrowDownRight, 
  X, 
  Edit2, 
  Target,
  AlertTriangle
} from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";

interface Position {
  id: string;
  symbol: string;
  type: "buy" | "sell";
  entryPrice: number;
  currentPrice: number;
  volume: number;
  stopLoss: number;
  takeProfit: number;
  pnl: number;
  pnlPercent: number;
  openTime: string;
  swap: number;
  commission: number;
}

interface PositionsTableProps {
  positions: Position[];
}

export function PositionsTable({ positions }: PositionsTableProps) {
  const [selectedPosition, setSelectedPosition] = useState<Position | null>(null);
  const [modifyDialogOpen, setModifyDialogOpen] = useState(false);
  const [newSL, setNewSL] = useState("");
  const [newTP, setNewTP] = useState("");

  const handleClosePosition = async (positionId: string) => {
    try {
      const response = await fetch(`/api/positions/${positionId}/close`, {
        method: "POST",
      });
      
      if (response.ok) {
        // Position closed successfully
        console.log("Position closed:", positionId);
      }
    } catch (error) {
      console.error("Error closing position:", error);
    }
  };

  const handleModifyPosition = async (positionId: string) => {
    try {
      const response = await fetch(`/api/positions/${positionId}/modify`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          stopLoss: parseFloat(newSL),
          takeProfit: parseFloat(newTP),
        }),
      });
      
      if (response.ok) {
        setModifyDialogOpen(false);
        console.log("Position modified:", positionId);
      }
    } catch (error) {
      console.error("Error modifying position:", error);
    }
  };

  const openModifyDialog = (position: Position) => {
    setSelectedPosition(position);
    setNewSL(position.stopLoss.toString());
    setNewTP(position.takeProfit.toString());
    setModifyDialogOpen(true);
  };

  const totalPnL = positions.reduce((sum, pos) => sum + pos.pnl, 0);

  return (
    <div>
      {/* Summary Header */}
      <div className="flex items-center justify-between mb-4 p-4 bg-slate-700/30 rounded-lg">
        <div className="flex items-center gap-4">
          <div>
            <p className="text-sm text-slate-400">إجمالي الربح/الخسارة</p>
            <p className={`text-xl font-bold ${totalPnL >= 0 ? "text-green-400" : "text-red-400"}`}>
              {totalPnL >= 0 ? "+" : ""}${totalPnL.toFixed(2)}
            </p>
          </div>
          <div className="h-8 w-px bg-slate-600" />
          <div>
            <p className="text-sm text-slate-400">عدد الصفقات</p>
            <p className="text-xl font-bold text-white">{positions.length}</p>
          </div>
        </div>
        
        {totalPnL < 0 && Math.abs(totalPnL) > 1000 && (
          <Badge variant="destructive" className="flex items-center gap-1">
            <AlertTriangle className="w-3 h-3" />
            مخاطرة عالية
          </Badge>
        )}
      </div>

      <ScrollArea className="h-[300px]">
        <Table>
          <TableHeader>
            <TableRow className="border-slate-700 hover:bg-transparent">
              <TableHead className="text-slate-400">الزوج</TableHead>
              <TableHead className="text-slate-400">النوع</TableHead>
              <TableHead className="text-slate-400">الحجم</TableHead>
              <TableHead className="text-slate-400">السعر</TableHead>
              <TableHead className="text-slate-400">الربح/الخسارة</TableHead>
              <TableHead className="text-slate-400">SL/TP</TableHead>
              <TableHead className="text-slate-400 text-left">الإجراءات</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <AnimatePresence>
              {positions.map((position, index) => (
                <motion.tr
                  key={position.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ delay: index * 0.05 }}
                  className="border-slate-700 hover:bg-slate-700/30"
                >
                  <TableCell className="font-medium text-white">
                    {position.symbol}
                  </TableCell>
                  <TableCell>
                    <Badge 
                      variant={position.type === "buy" ? "default" : "destructive"}
                      className={position.type === "buy" ? "bg-green-600" : "bg-red-600"}
                    >
                      {position.type === "buy" ? (
                        <ArrowUpRight className="w-3 h-3 mr-1" />
                      ) : (
                        <ArrowDownRight className="w-3 h-3 mr-1" />
                      )}
                      {position.type === "buy" ? "شراء" : "بيع"}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-slate-300">
                    {position.volume.toFixed(2)}
                  </TableCell>
                  <TableCell>
                    <div className="text-slate-300">
                      <div>{position.entryPrice.toFixed(5)}</div>
                      <div className="text-xs text-slate-500">
                        الحالي: {position.currentPrice.toFixed(5)}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className={`font-bold ${position.pnl >= 0 ? "text-green-400" : "text-red-400"}`}>
                      {position.pnl >= 0 ? "+" : ""}${position.pnl.toFixed(2)}
                      <span className="text-xs block">
                        ({position.pnlPercent >= 0 ? "+" : ""}{position.pnlPercent.toFixed(2)}%)
                      </span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="text-xs text-slate-400">
                      <div className="text-red-400">SL: {position.stopLoss.toFixed(5)}</div>
                      <div className="text-green-400">TP: {position.takeProfit.toFixed(5)}</div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-blue-400 hover:text-blue-300"
                        onClick={() => openModifyDialog(position)}
                      >
                        <Edit2 className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-red-400 hover:text-red-300"
                        onClick={() => handleClosePosition(position.id)}
                      >
                        <X className="w-4 h-4" />
                      </Button>
                    </div>
                  </TableCell>
                </motion.tr>
              ))}
            </AnimatePresence>
            
            {positions.length === 0 && (
              <TableRow>
                <TableCell colSpan={7} className="text-center py-8 text-slate-500">
                  لا توجد صفقات مفتوحة حالياً
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </ScrollArea>

      {/* Modify Dialog */}
      <Dialog open={modifyDialogOpen} onOpenChange={setModifyDialogOpen}>
        <DialogContent className="bg-slate-800 border-slate-700">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Target className="w-5 h-5 text-blue-500" />
              تعديل الصفقة
            </DialogTitle>
          </DialogHeader>
          
          {selectedPosition && (
            <div className="space-y-4 mt-4">
              <div className="p-3 bg-slate-700/50 rounded-lg">
                <p className="text-sm text-slate-400">الزوج: <span className="text-white">{selectedPosition.symbol}</span></p>
                <p className="text-sm text-slate-400">النوع: 
                  <span className={selectedPosition.type === "buy" ? "text-green-400" : "text-red-400"}>
                    {selectedPosition.type === "buy" ? " شراء" : " بيع"}
                  </span>
                </p>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="sl" className="text-slate-300">Stop Loss جديد</Label>
                <Input
                  id="sl"
                  type="number"
                  step="0.00001"
                  value={newSL}
                  onChange={(e) => setNewSL(e.target.value)}
                  className="bg-slate-700 border-slate-600 text-white"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="tp" className="text-slate-300">Take Profit جديد</Label>
                <Input
                  id="tp"
                  type="number"
                  step="0.00001"
                  value={newTP}
                  onChange={(e) => setNewTP(e.target.value)}
                  className="bg-slate-700 border-slate-600 text-white"
                />
              </div>
              
              <div className="flex gap-2 mt-4">
                <Button
                  variant="outline"
                  onClick={() => setModifyDialogOpen(false)}
                  className="flex-1"
                >
                  إلغاء
                </Button>
                <Button
                  onClick={() => handleModifyPosition(selectedPosition.id)}
                  className="flex-1 bg-blue-600 hover:bg-blue-700"
                >
                  حفظ التغييرات
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
